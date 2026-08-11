class ECGMonitor:

    def __init__(
        self,
        tachycardia_threshold=100,
        bradycardia_threshold=60,
        required_beats=3,
        rr_history_size=5,
        irregular_threshold=0.20
    ):

        self.tachycardia_threshold = tachycardia_threshold
        self.bradycardia_threshold = bradycardia_threshold
        self.required_beats = required_beats

        # Irregular rhythm settings
        self.rr_history_size = rr_history_size
        self.irregular_threshold = irregular_threshold
        self.rr_history = []

        self.high_count = 0
        self.low_count = 0
        self.normal_count = 0

        self.status = "NORMAL"


    def update(self, bpm, rr=None):

        # ------------------------------------------
        # No BPM yet
        # ------------------------------------------

        if bpm is None:

            return {
                "status": self.status,
                "alert": self.status != "NORMAL"
            }


        # ------------------------------------------
        # Store RR interval
        # ------------------------------------------

        if rr is not None:

            self.rr_history.append(rr)

            if len(self.rr_history) > self.rr_history_size:

                self.rr_history.pop(0)


        # ------------------------------------------
        # Tachycardia
        # ------------------------------------------

        if bpm > self.tachycardia_threshold:

            self.high_count += 1
            self.low_count = 0
            self.normal_count = 0

        # ------------------------------------------
        # Bradycardia
        # ------------------------------------------

        elif bpm < self.bradycardia_threshold:

            self.low_count += 1
            self.high_count = 0
            self.normal_count = 0

        # ------------------------------------------
        # Normal BPM
        # ------------------------------------------

        else:

            self.normal_count += 1

            self.high_count = 0
            self.low_count = 0


        # ------------------------------------------
        # Determine tachy / brady
        # ------------------------------------------

        if self.high_count >= self.required_beats:

            self.status = "TACHYCARDIA"

        elif self.low_count >= self.required_beats:

            self.status = "BRADYCARDIA"


        # ------------------------------------------
        # Irregular rhythm
        # ------------------------------------------

        if len(self.rr_history) >= 4:

            mean_rr = sum(self.rr_history) / len(self.rr_history)

            if mean_rr > 0:

                max_deviation = max(
                    abs(rr_value - mean_rr)
                    for rr_value in self.rr_history
                )

                relative_deviation = (
                    max_deviation / mean_rr
                )

                if relative_deviation > self.irregular_threshold:

                    self.status = "IRREGULAR"


        # ------------------------------------------
        # Return to normal
        # ------------------------------------------

        if (
            self.status == "NORMAL"
            and self.normal_count >= self.required_beats
        ):

            self.status = "NORMAL"


        return {
            "status": self.status,
            "alert": self.status != "NORMAL"
        }
