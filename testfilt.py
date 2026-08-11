import wfdb
import numpy as np

from filters import HighPassFilter, LowPassFilter, EMAFilter


# Load ECG
patient_data = "Person_01/rec_5"

ecg = wfdb.rdrecord(patient_data)

signal = ecg.p_signal[:, 0]

fs = 500


# Create filters
highpass = HighPassFilter(
    cutoff=5,
    fs=fs
)

lowpass = LowPassFilter(
    cutoff=12,
    fs=fs
)

ema = EMAFilter(
    alpha=0.2
)


# Process sample-by-sample
filtered = []

for sample in signal:

    hp = highpass.process(sample)

    lp = lowpass.process(hp)

    smoothed = ema.process(lp)

    filtered.append(smoothed)


filtered = np.array(filtered)

print("Raw samples:", len(signal))
print("Filtered samples:", len(filtered))

print("First 10 filtered samples:")
print(filtered[:10])
