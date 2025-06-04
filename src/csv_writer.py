import csv
from io import StringIO

def generate_time_column(metadata, total_samples):
    times = []
    current_time = 0.0
    sample_idx = 0
    time_step = 0
    for samp, endsamp in metadata['sampling_rates']:
        if samp == 0:
            raise ValueError(f"Invalid sampling rate (samp=0) for endsamp={endsamp}. Please check your .CFG file.")
        time_step = 1 / samp
        while sample_idx <= endsamp and sample_idx < total_samples:
            times.append(round(current_time, 6))
            current_time += time_step
            sample_idx += 1
    while len(times) < total_samples:
        times.append(round(current_time, 6))
        current_time += time_step
    return times

def write_csv(metadata, channels, data):
    """Returns CSV content as a string (for uploading to blob storage)."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ['Time'] +
        [
            f"{ch['name']} ({ch['unit']})" if ch['type'] == 'analog' and ch['unit']
            else ch['name']
            for ch in channels
        ]
    )
    times = generate_time_column(metadata, len(data))
    for t, row in zip(times, data):
        writer.writerow([f"{t:.6f}"] + list(row))
    return output.getvalue()