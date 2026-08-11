import wfdb


class WFDBSource:

    def __init__(self, record_path, channel=0):

        record = wfdb.rdrecord(record_path)

        self.signal = record.p_signal[:, channel]

    def samples(self):

        for index, sample in enumerate(self.signal):

            yield index, sample

class SimulatedECGSource:

    def __init__(self, record_path, channel=0):

        record = wfdb.rdrecord(record_path)

        self.signal = record.p_signal[:, channel]

    def samples(self):

        for index, sample in enumerate(self.signal):

            yield index, sample
