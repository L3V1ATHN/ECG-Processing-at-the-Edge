import os
import glob
import re
import numpy as np


class ECGRecorder:

    def __init__(
        self,
        output_dir="recordings",
        chunk_size=100000,
        dtype=np.float32
    ):

        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.dtype = dtype

        os.makedirs(
            self.output_dir,
            exist_ok=True
        )

        self.buffer = []

        # Continue from the next available chunk number.
        existing_files = glob.glob(
            os.path.join(
                self.output_dir,
                "chunk_*.dat"
            )
        )

        numbers = []

        for filename in existing_files:

            match = re.search(
                r"chunk_(\d+)\.dat$",
                os.path.basename(filename)
            )

            if match:
                numbers.append(
                    int(match.group(1))
                )

        self.chunk_number = (
            max(numbers) + 1
            if numbers
            else 0
        )

        self.total_samples = 0

    def add_sample(self, sample):

        self.buffer.append(sample)
        self.total_samples += 1

        if len(self.buffer) >= self.chunk_size:
            self.save_chunk()

    def save_chunk(self):

        if not self.buffer:
            return

        filename = os.path.join(
            self.output_dir,
            f"chunk_{self.chunk_number:06d}.dat"
        )

        data = np.asarray(
            self.buffer,
            dtype=self.dtype
        )

        data.tofile(filename)

        print(
            f"Saved {filename} "
            f"({len(data)} samples)"
        )

        self.buffer.clear()
        self.chunk_number += 1

    def close(self):

        if self.buffer:
            self.save_chunk()

        print(
            f"Recording complete. "
            f"Total samples: {self.total_samples}"
        )
