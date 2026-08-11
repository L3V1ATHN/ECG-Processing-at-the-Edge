import wfdb

from processor import ECGProcessor


patient_data = "Person_01/rec_5"

ecg = wfdb.rdrecord(patient_data)

signal = ecg.p_signal[:, 0]

fs = 500


processor = ECGProcessor(fs=fs)


r_peaks = []


for index, sample in enumerate(signal):

    result = processor.process(
        sample,
        index
    )

    if result["peak"]:

        r_peaks.append(
            result["peak_index"]
        )

        print(
            "R-PEAK:",
            result["peak_index"]
        )

        if result["bpm"] is not None:

            print(
                "BPM:",
                result["bpm"]
            )


print()
print("Total R-peaks:", len(r_peaks))
