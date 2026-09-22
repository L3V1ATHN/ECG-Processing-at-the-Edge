import os
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from auth_data import DOCTORS, PATIENTS, patient_for_username
from processor import ECGProcessor
from data_source import SimulatedECGSource

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "ecg-demo-secret-change-me")
socketio = SocketIO(app)

@app.route("/")
def home():
    if session.get("role") == "doctor":
        return redirect(url_for("doctor_dashboard"))
    if session.get("role") == "patient":
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("role"))


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                return redirect(url_for(f"{role}_login"))
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


@app.route("/role")
def role():
    return render_template("role.html")


@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        doctor = DOCTORS.get(username)
        if doctor and doctor["password"] == request.form.get("password"):
            session.clear()
            session.update(role="doctor", username=username)
            return redirect(url_for("doctor_dashboard"))
        flash("Invalid doctor username or password.", "error")
    return render_template("login.html", role="Doctor")


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


@app.route("/patient/login", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        patient_id, patient = patient_for_username(request.form.get("username", "").strip())
        if patient and patient["password"] == request.form.get("password"):
            session.clear()
            session.update(role="patient", username=patient["username"], patient_id=patient_id,
                           selected_patient_id=patient_id)
            return redirect(url_for("patient_dashboard"))
        flash("Invalid patient username or password.", "error")
    return render_template("login.html", role="Patient")


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
    return render_template("index.html", patient_id=patient_id, patient=patient,
                           doctor=DOCTORS[patient["doctor"]])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("role"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("access_denied.html", message="You are not authorized to view this patient data."), 403

def send_ecg_data(patient_id, sid):
    patient = PATIENTS[patient_id]
    try:
        source = SimulatedECGSource(patient["record"])
        processor = ECGProcessor(fs=patient["sampling_rate"])

        for index, sample in source.samples():
            result = processor.process(sample, index)
            socketio.emit("ecg_data", {
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
            }, to=sid)
            socketio.sleep(1 / patient["sampling_rate"])
        socketio.emit("stream_end", to=sid)
    except Exception:
        app.logger.exception("Unable to stream ECG record %s", patient_id)
        socketio.emit("stream_error", {"message": "Unable to load this ECG record."}, to=sid)
@socketio.on("connect")
def handle_connect(auth=None):
    patient_id, _patient = selected_patient_is_authorized()
    if not patient_id:
        return False
    socketio.start_background_task(send_ecg_data, patient_id, request.sid)


if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False)
