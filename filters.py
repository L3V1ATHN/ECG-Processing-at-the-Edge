import numpy as np


class HighPassFilter:
    def __init__(self, cutoff, fs):
        dt = 1 / fs
        RC = 1 / (2 * np.pi * cutoff)

        self.alpha = RC / (RC + dt)

        self.previous_input = 0.0
        self.previous_output = 0.0

    def process(self, x):
        y = self.alpha * (
            self.previous_output
            + x
            - self.previous_input
        )

        self.previous_input = x
        self.previous_output = y

        return y


class LowPassFilter:
    def __init__(self, cutoff, fs):
        dt = 1 / fs
        RC = 1 / (2 * np.pi * cutoff)

        self.alpha = dt / (RC + dt)

        self.previous_output = 0.0

    def process(self, x):
        y = self.previous_output + self.alpha * (
            x - self.previous_output
        )

        self.previous_output = y

        return y


class EMAFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.previous_output = 0.0
        self.initialized = False

    def process(self, x):

        if not self.initialized:
            self.previous_output = x
            self.initialized = True
            return x

        y = (
            self.alpha * x
            + (1 - self.alpha) * self.previous_output
        )

        self.previous_output = y

        return y
