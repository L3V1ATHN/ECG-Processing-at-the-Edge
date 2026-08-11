from monitor import ECGMonitor

monitor = ECGMonitor()

test_bpm = [
    82,
    80,
    58,
    55,
    54,
    53
]

for bpm in test_bpm:

    result = monitor.update(bpm)

    print(
        f"BPM: {bpm:>3} | "
        f"Status: {result['status']:<12} | "
        f"Alert: {result['alert']}"
    )
