import wfdb
import numpy as np

from filters import HighPassFilter, LowPassFilter, EMAFilter
from detector import PeakDetector


patient_data = "Person_01/rec_5"

ecg = wfdb.rdrecord(patient_data)

signal = ecg.p_signal[:, 0]

fs = 500


# Filters
highpass = HighPassFilter(cutoff=5, fs=fs)
lowpass = LowPassFilter(cutoff=12, fs=fs)
ema = EMAFilter(alpha=0.2)


# Peak detector
detector = PeakDetector(
    fs=fs,
    threshold_ratio=0.3,
    refractory=0.2
)


r_peaks = []


# Process entire recording one sample at a time
for index, sample in enumerate(signal):

    hp = highpass.process(sample)

    lp = lowpass.process(hp)

    filtered = ema.process(lp)

    squared = filtered ** 2

    peak = detector.process(squared, index)

    if peak is not None:
        r_peaks.append(peak)


r_peaks = np.array(r_peaks)


print("Number of R-peaks:", len(r_peaks))

print("Peak locations:")
print(r_peaks)


# Calculate HR
if len(r_peaks) > 1:

    rr_intervals = np.diff(r_peaks) / fs

    hr = 60 / rr_intervals

    print("\nHeart rates:")
    print(hr)
