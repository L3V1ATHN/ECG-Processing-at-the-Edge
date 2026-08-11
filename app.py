from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
from filters import HighPassFilter, LowPassFilter, EMAFilter
from detector import PeakDetector

import wfdb
import numpy as np
from data_source import WFDBSource
from processor import ECGProcessor
from data_source import SimulatedECGSource

app = Flask(__name__)
socketio = SocketIO(app)

thread = None

@app.route("/")
def home():
    return render_template("index.html")

def send_ecg_data():

    fs = 500

    source = SimulatedECGSource(
       #"demos/Normal/rec_5"
       #"demos/Normal/rec_8"
       #"demos/Tach/rec_1"
       #"demos/Brad/rec_1"
       "demos/Irr/rec_2"
    )

    processor = ECGProcessor(fs=fs)

    for index, sample in source.samples():

        print(f"STREAM: {index}")
        result = processor.process(
            sample,
            index
        )

        socketio.emit(
            "ecg_data",
            {
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
        )

        socketio.sleep(1 / fs)

    print("ECG STREAM FINISHED")

    socketio.emit("stream_end")
@socketio.on("connect")
def handle_connect(auth=None):
    global thread

    print("Client connected!")

    if thread is None:
        thread = socketio.start_background_task(send_ecg_data)


if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False)
