import struct
from datetime import datetime, timedelta

def parse_cfg(cfg_content):
    metadata = {}
    channels = []
    sampling_rates = []
    n_analog = 0
    n_digital = 0

    lines = [line.strip() for line in cfg_content.splitlines()]

    # Skip the first 2 lines (header info)
    channel_lines = lines[2:]

    channel_end = 0
    for i, line in enumerate(lines):
        parts = line.split(',')
        if len(parts) >= 3 and parts[0].isdigit():
            channel_end = i

    # Adjust for the skipped lines
    channel_end += 2

    total_channels = int(lines[channel_end + 1])
    nrates = int(lines[channel_end + 2])
    metadata['nrates'] = nrates

    for i in range(nrates):
        parts = lines[channel_end + 3 + i].split(',')
        if len(parts) == 2:
            sampling_rates.append((float(parts[0]), int(parts[1])))
    metadata['sampling_rates'] = sampling_rates

    for line in lines[2:channel_end + 1]:
        parts = line.split(',')
        if parts and parts[0].isdigit():
            # Analog channel
            if len(parts) >= 6:
                channels.append({
                    'index': int(parts[0]),
                    'name': parts[1],
                    'unit': parts[4],
                    'scale': float(parts[5]),
                    'type': 'analog'
                })
                n_analog += 1
            # Digital channel (handle 3, 4, or 5 fields)
            elif 3 <= len(parts) <= 5:
                channels.append({
                    'index': int(parts[0]),
                    'name': parts[1],
                    'unit': parts[2] if len(parts) > 2 else '',
                    'scale': 1.0,
                    'type': 'digital'
                })
                n_digital += 1

    metadata['n_analog'] = n_analog
    metadata['n_digital'] = n_digital
    return metadata, channels


def parse_dat(dat_content, channels, metadata):
    data = []
    n_analog = metadata['n_analog']
    n_digital = metadata['n_digital']
    digital_bytes = 2 * ((n_digital + 15) // 16) if n_digital > 0 else 0
    row_size = 2 * n_analog + digital_bytes

    # Prepare for timestamp calculation
    sampling_rates = metadata.get('sampling_rates', [(1.0, 0)])
    start_datetime = metadata.get('start_datetime', None)
    sample_idx = 0
    rate_idx = 0
    rate_sample_count = 0
    if sampling_rates:
        current_rate, current_count = sampling_rates[rate_idx]
    else:
        current_rate, current_count = 1.0, 0

    offset = 0
    while offset + row_size <= len(dat_content):
        chunk = dat_content[offset:offset + row_size]
        analogs = struct.unpack(f'<{n_analog}h', chunk[:2 * n_analog])
        digitals = []
        for i in range(0, digital_bytes, 2):
            word = struct.unpack('<H', chunk[2 * n_analog + i:2 * n_analog + i + 2])[0]
            for bit in range(16):
                digitals.append((word >> bit) & 1)
        digitals = digitals[:n_digital]
        analog_scaled = [v * ch['scale'] for v, ch in zip(analogs, channels[:n_analog])]

        # Calculate timestamp if possible
        if start_datetime:
            # If we've exhausted the current rate's sample count, move to next rate
            if rate_sample_count >= current_count and rate_idx + 1 < len(sampling_rates):
                rate_idx += 1
                current_rate, current_count = sampling_rates[rate_idx]
                rate_sample_count = 0
            # Calculate time offset for this sample
            time_offset = sum(
                count / rate for rate, count in sampling_rates[:rate_idx]
            ) + (rate_sample_count / current_rate if current_rate else 0)
            timestamp = start_datetime + timedelta(seconds=time_offset)
            row = [timestamp] + analog_scaled + digitals
        else:
            row = analog_scaled + digitals

        data.append(row)
        offset += row_size
        sample_idx += 1
        rate_sample_count += 1
    return data
