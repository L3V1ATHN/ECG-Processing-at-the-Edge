from filters import HighPassFilter, LowPassFilter, EMAFilter
from detector import PeakDetector
from monitor import ECGMonitor

class ECGProcessor:

    def __init__(self, fs=500):

        self.monitor = ECGMonitor()
        self.fs = fs

        # Filters
        self.highpass = HighPassFilter(
            cutoff=5,
            fs=fs
        )

        self.lowpass = LowPassFilter(
            cutoff=12,
            fs=fs
        )

        self.ema = EMAFilter(
            alpha=0.2
        )

        # R-peak detector
        self.detector = PeakDetector(
            fs=fs,
            threshold_ratio=0.25,
            refractory=0.2
        )

        # Previous R-peak
        self.previous_peak = None


    def process(self, sample, index):

        # -----------------
        # Filtering
        # -----------------

        hp = self.highpass.process(sample)

        lp = self.lowpass.process(hp)

        filtered = self.ema.process(lp)


        # -----------------
        # Squaring
        # -----------------

        squared = filtered ** 2


        # -----------------
        # R-peak detection
        # -----------------

        result = self.detector.process(
            squared,
            index
        )


        peak = None
        peak_value = None
        bpm = None
        monitor_result = {
            "status": self.monitor.status,
            "alert": self.monitor.status != "NORMAL"
        }

        if result is not None:

            peak, peak_value = result

            # Calculate BPM
            if self.previous_peak is not None:

                rr = (peak - self.previous_peak) / self.fs

                bpm = 60 / rr
                monitor_result = self.monitor.update(
                                    bpm,
                                    rr
                                )

            self.previous_peak = peak


        return {
    "index": index,

    "raw": float(sample),
    "filtered": float(filtered),
    "squared": float(squared),

    "peak": peak is not None,
    "peak_index": peak,
    "peak_value": peak_value,

    "bpm": bpm,

    "status": monitor_result["status"],
    "alert": monitor_result["alert"]
}
