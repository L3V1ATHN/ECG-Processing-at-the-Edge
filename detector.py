from collections import deque


class PeakDetector:

    def __init__(
        self,
        fs,
        threshold_ratio=0.5,
        refractory=0.2,
        rolling_window=3.0,
        peak_confirmation=0.15,
    ):
        self.fs = fs
        self.threshold_ratio = threshold_ratio

        self.refractory_samples = int(refractory * fs)

        # How long we wait before confirming a candidate peak.
        self.confirmation_samples = int(
            peak_confirmation * fs
        )

        # Rolling maximum
        self.rolling_window_samples = int(
            rolling_window * fs
        )

        self.rolling_max = deque()

        self.previous_previous = None
        self.previous = None

        self.last_peak = -float("inf")

        self.startup_samples = fs
        self.sample_count = 0

        # Candidate peak
        self.candidate_index = None
        self.candidate_value = None
        self.candidate_age = 0

    def process(self, sample, index):

        self.sample_count += 1

        # ------------------------------------------------
        # Rolling maximum
        # ------------------------------------------------

        while (
            self.rolling_max
            and self.rolling_max[0][0]
            <= index - self.rolling_window_samples
        ):
            self.rolling_max.popleft()

        while (
            self.rolling_max
            and self.rolling_max[-1][1] <= sample
        ):
            self.rolling_max.pop()

        self.rolling_max.append((index, sample))

        rolling_max = self.rolling_max[0][1]

        # ------------------------------------------------
        # Initialize
        # ------------------------------------------------

        if self.previous_previous is None:
            self.previous_previous = sample
            return None

        if self.previous is None:
            self.previous = sample
            return None

        # ------------------------------------------------
        # Startup
        # ------------------------------------------------

        if self.sample_count <= self.startup_samples:

            self.previous_previous = self.previous
            self.previous = sample

            return None

        # ------------------------------------------------
        # Current local maximum
        # ------------------------------------------------

        is_peak = (
            self.previous > self.previous_previous
            and self.previous >= sample
        )

        threshold = self.threshold_ratio * rolling_max

        # ------------------------------------------------
        # Candidate handling
        # ------------------------------------------------

        if is_peak:

            peak_index = index - 1
            peak_value = self.previous

            above_threshold = peak_value >= threshold

            if above_threshold:

                # ----------------------------------------
                # No candidate yet
                # ----------------------------------------

                if self.candidate_index is None:

                    self.candidate_index = peak_index
                    self.candidate_value = peak_value
                    self.candidate_age = 0

                # ----------------------------------------
                # New peak is higher
                # ----------------------------------------

                elif peak_value > self.candidate_value:

                    print(
                        "REPLACING CANDIDATE:",
                        self.candidate_index,
                        self.candidate_value,
                        "->",
                        peak_index,
                        peak_value,
                    )

                    self.candidate_index = peak_index
                    self.candidate_value = peak_value
                    self.candidate_age = 0

        # ------------------------------------------------
        # Age candidate
        # ------------------------------------------------

        if self.candidate_index is not None:

            self.candidate_age += 1

            # ------------------------------------------------
            # Confirm candidate
            # ------------------------------------------------

            if self.candidate_age >= self.confirmation_samples:

                candidate_index = self.candidate_index
                candidate_value = self.candidate_value

                far_enough = (
                    candidate_index - self.last_peak
                    > self.refractory_samples
                )

                print(
                    "CONFIRMED PEAK:",
                    candidate_index,
                    "value=",
                    candidate_value,
                    "rolling_max=",
                    rolling_max,
                    "far_enough=",
                    far_enough,
                )

                self.candidate_index = None
                self.candidate_value = None
                self.candidate_age = 0

                if far_enough:

                    self.last_peak = candidate_index

                    self.previous_previous = self.previous
                    self.previous = sample

                    return candidate_index, candidate_value

        # ------------------------------------------------
        # Advance
        # ------------------------------------------------

        self.previous_previous = self.previous
        self.previous = sample

        return None
