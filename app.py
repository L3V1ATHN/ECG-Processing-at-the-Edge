import os
import numpy as np
from pathlib import Path
from datetime import datetime
from functools import wraps
from storage import ECGRecorder
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from auth_data import DOCTORS, PATIENTS, patient_for_username
from processor import ECGProcessor
from data_source import SimulatedECGSource
import threading

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "ecg-demo-secret-change-me")
socketio = SocketIO(app)

# Process-local audit history; each patient retains every successful ECG open.
ACCESS_LOG = []
LATEST_ACCESS = {}

# --------------------------------------------------
# ECG recording state
# --------------------------------------------------

RECORDERS = {}
RECORDING = {}
RECORDER_LOCK = threading.Lock()

def patient_access_history(patient_id, limit=2):
    """Return the most recent successful access events for one patient."""
    return [event for event in reversed(ACCESS_LOG)
            if event["patient_id"] == patient_id][:limit]

@app.route("/")
def home():
    if session.get("role") == "doctor":
        return redirect(url_for("doctor_dashboard"))
    if session.get("role") == "patient":
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("login"))


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def selected_patient_is_authorized():
    patient_id = session.get("selected_patient_id")
    patient = PATIENTS.get(patient_id)
    if not patient:
        return None, None
    if session.get("role") == "doctor" and patient["doctor"] == session.get("username"):
        return patient_id, patient
    if session.get("role") == "patient" and patient_id == session.get("patient_id"):
        return patient_id, patient
    return None, None


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("role") == "doctor":
        return redirect(url_for("doctor_dashboard"))
    if session.get("role") == "patient":
        return redirect(url_for("patient_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        doctor = DOCTORS.get(username)
        if doctor and doctor["password"] == request.form.get("password"):
            session.clear()
            session.update(role="doctor", username=username, name=doctor["name"], user_id=username)
            return redirect(url_for("doctor_dashboard"))
        patient_id, patient = patient_for_username(username)
        if patient and patient["password"] == request.form.get("password"):
            session.clear()
            session.update(role="patient", username=username, name=patient["name"],
                           user_id=patient_id, patient_id=patient_id,
                           selected_patient_id=patient_id)
            return redirect(url_for("patient_dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/doctor/dashboard")
@role_required("doctor")
def doctor_dashboard():
    doctor = DOCTORS[session["username"]]
    patients = [{"id": patient_id, **patient} for patient_id, patient in PATIENTS.items()
                if patient["doctor"] == session["username"]]
    return render_template("doctor_dashboard.html", doctor=doctor, patients=patients)


@app.route("/doctor/patient/<patient_id>")
@role_required("doctor")
def doctor_patient(patient_id):
    patient = PATIENTS.get(patient_id)
    if not patient or patient["doctor"] != session.get("username"):
        abort(403)
    session["selected_patient_id"] = patient_id
    return render_ecg_dashboard(patient_id)


@app.route("/patient/dashboard")
@role_required("patient")
def patient_dashboard():
    return render_ecg_dashboard(session["patient_id"])


@app.route("/patient/<patient_id>")
@role_required("patient")
def patient_record(patient_id):
    if patient_id != session.get("patient_id"):
        abort(403)
    return render_ecg_dashboard(patient_id)


def render_ecg_dashboard(patient_id):
    patient = PATIENTS.get(patient_id)
    if not patient:
        abort(404)
    if not os.path.isfile(f"{patient['record']}.hea") or not os.path.isfile(f"{patient['record']}.dat"):
        return render_template("access_denied.html", message="The assigned ECG record is missing."), 404
    accessed_at = datetime.now().astimezone()
    accessor = {
        "patient_id": patient_id,
        "accessed_by": session["username"],
        "accessor_name": session["name"],
        "accessor_role": session["role"],
        "timestamp": accessed_at.isoformat(timespec="seconds"),
        "display_timestamp": accessed_at.strftime("%d %B %Y, %I:%M %p"),
    }
    prior_accesses = patient_access_history(patient_id)
    page = render_template("index.html", patient_id=patient_id, patient=patient,
                           doctor=DOCTORS[patient["doctor"]], last_access=accessor,
                           access_history=([accessor] + prior_accesses)[:2])
    ACCESS_LOG.append(accessor)
    LATEST_ACCESS[patient_id] = accessor
    return page


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("access_denied.html", message="You are not authorized to view this patient data."), 403

def start_recording(patient_id):

    with RECORDER_LOCK:

        if RECORDING.get(patient_id, False):
            return False

        output_dir = os.path.join(
            "recordings",
            patient_id
        )

        os.makedirs(output_dir, exist_ok=True)

        # Remove previous recording chunks
        for filename in os.listdir(output_dir):

            if (
                filename.startswith("chunk_")
                and filename.endswith(".dat")
            ):
                os.remove(
                    os.path.join(output_dir, filename)
                )

        recorder = ECGRecorder(
            output_dir=output_dir,
            chunk_size=100000
        )

        RECORDERS[patient_id] = recorder
        RECORDING[patient_id] = True

        app.logger.info(
            "Started ECG recording for %s",
            patient_id
        )

        return True


def stop_recording(patient_id):
    with RECORDER_LOCK:

        recorder = RECORDERS.pop(patient_id, None)
        RECORDING[patient_id] = False

        if recorder is not None:
            recorder.close()

            app.logger.info(
                "Stopped ECG recording for %s",
                patient_id
            )

            return True

        return False

def make_ecg_payload(result, index):
    return {
        "index": index,

        "raw": result["raw"],
        "filtered": result["filtered"],
        "squared": result["squared"],

        "peak": result["peak"],
        "peak_index": result["peak_index"],
        "peak_value": result["peak_value"],

        "bpm": result["bpm"],

        "status": result["status"],
        "alert": result["alert"]
    }


def send_ecg_data(patient_id, sid):

    patient = PATIENTS[patient_id]

    try:

        source = SimulatedECGSource(patient["record"])
        processor = ECGProcessor(
            fs=patient["sampling_rate"]
        )

        for index, sample in source.samples():

            # ------------------------------------------
            # Store raw ECG sample if recording is active
            # ------------------------------------------

            with RECORDER_LOCK:

                recorder = RECORDERS.get(patient_id)

                if recorder and RECORDING.get(patient_id, False):
                    recorder.add_sample(sample)

            # ------------------------------------------
            # Process ECG
            # ------------------------------------------

            result = processor.process(
                sample,
                index
            )

            # ------------------------------------------
            # Send to browser
            # ------------------------------------------

            socketio.emit(
                "ecg_data",
                make_ecg_payload(result, index),
                to=sid
            )

            socketio.sleep(
                1 / patient["sampling_rate"]
            )

        # Simulation finished
        socketio.emit(
            "stream_end",
            to=sid
        )

    except Exception:

        app.logger.exception(
            "Unable to stream ECG record %s",
            patient_id
        )

        socketio.emit(
            "stream_error",
            {
                "message": "Unable to load this ECG record."
            },
            to=sid
        )

    finally:

        if RECORDING.get(patient_id, False):

            stop_recording(patient_id)

            socketio.emit(
            "recording_status",
            {
                "recording": False
            },
            to=sid
        )

def send_stored_data(patient_id, sid):

    patient = PATIENTS[patient_id]

    try:

        recording_dir = Path(
            "recordings",
            patient_id
        )

        chunk_files = sorted(
            recording_dir.glob("chunk_*.dat")
        )

        if not chunk_files:

            socketio.emit(
                "stored_data_error",
                {
                    "message": "No stored ECG dataset found."
                },
                to=sid
            )

            return

        # Re-create the processor so the stored raw ECG
        # produces filtered/squared/peak data again.
        processor = ECGProcessor(
            fs=patient["sampling_rate"]
        )

        socketio.emit(
            "stored_data_start",
            to=sid
        )

        index = 0
        batch = []

        for chunk_file in chunk_files:

            data = np.fromfile(
                chunk_file,
                dtype=np.float32
            )

            for sample in data:

                result = processor.process(
                    float(sample),
                    index
                )

                batch.append(
                    make_ecg_payload(
                        result,
                        index
                    )
                )

                index += 1

                # Send 250 samples at a time instead of
                # creating one WebSocket message per sample.
                if len(batch) >= 250:

                    socketio.emit(
                        "stored_ecg_batch",
                        {
                            "samples": batch
                        },
                        to=sid
                    )

                    batch = []

                    # Give Socket.IO a chance to handle
                    # other events.
                    socketio.sleep(0)

        # Send remaining samples
        if batch:

            socketio.emit(
                "stored_ecg_batch",
                {
                    "samples": batch
                },
                to=sid
            )

        socketio.emit(
            "stored_data_end",
            to=sid
        )

    except Exception:

        app.logger.exception(
            "Unable to load stored ECG data for %s",
            patient_id
        )

        socketio.emit(
            "stored_data_error",
            {
                "message": "Unable to load stored ECG dataset."
            },
            to=sid
        )

@socketio.on("connect")
def handle_connect(auth=None):

    patient_id, _patient = selected_patient_is_authorized()

    if not patient_id:
        return False

    # Start recording automatically when the ECG page loads.
    recording_started = start_recording(patient_id)

    socketio.emit(
        "recording_status",
        {
            "recording": (
                recording_started
                or RECORDING.get(patient_id, False)
            )
        },
        to=request.sid
    )

    # Start the ECG stream.
    socketio.start_background_task(
        send_ecg_data,
        patient_id,
        request.sid
    )

@socketio.on("stop_recording")
def handle_stop_recording():

    patient_id, _patient = selected_patient_is_authorized()

    if not patient_id:
        return

    stop_recording(patient_id)

    socketio.emit(
        "recording_status",
        {
            "recording": False
        },
        to=request.sid
    )


@socketio.on("load_stored_data")
def handle_load_stored_data():

    patient_id, _patient = selected_patient_is_authorized()

    if not patient_id:
        return

    # Make sure the latest partial chunk is saved
    # before loading the dataset.
    if RECORDING.get(patient_id, False):
        stop_recording(patient_id)

    socketio.start_background_task(
        send_stored_data,
        patient_id,
        request.sid
    )
if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False)
