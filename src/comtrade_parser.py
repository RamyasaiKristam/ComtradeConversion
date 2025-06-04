import struct
from datetime import datetime, timedelta

def parse_cfg(cfg_content):
    metadata = {}
    channels = []
    sampling_rates = []
    n_analog = 0
    n_digital = 0

    lines = [line.strip() for line in cfg_content.splitlines()]

    # Parse channel count from line 1
    channel_count_line = lines[1].split(',')
    total_channels = int(channel_count_line[0])
    n_analog = int(channel_count_line[1][:-1])  # Remove 'A'
    n_digital = int(channel_count_line[2][:-1])  # Remove 'D'

    # Parse channel definitions
    for i in range(2, 2 + total_channels):
        parts = lines[i].split(',')
        if len(parts) >= 6 and i - 2 < n_analog:
            # Analog channel
            channels.append({
                'index': int(parts[0]),
                'name': parts[1],
                'phase': parts[2] if len(parts) > 2 else '',
                'circuit': parts[3] if len(parts) > 3 else '',
                'unit': parts[4] if len(parts) > 4 else '',
                'scale': float(parts[5]) if len(parts) > 5 else 1.0,
                'a': float(parts[5]) if len(parts) > 5 else 1.0,
                'b': float(parts[6]) if len(parts) > 6 else 0.0,
                'skew': float(parts[7]) if len(parts) > 7 else 0.0,
                'min': float(parts[8]) if len(parts) > 8 else None,
                'max': float(parts[9]) if len(parts) > 9 else None,
                'primary': float(parts[10]) if len(parts) > 10 else 1.0,
                'secondary': float(parts[11]) if len(parts) > 11 else 1.0,
                'ps': parts[12].strip().upper() if len(parts) > 12 else '',
                'type': 'analog'
            })
        elif 3 <= len(parts) <= 5:
            # Digital channel
            channels.append({
                'index': int(parts[0]),
                'name': parts[1],
                'unit': parts[2] if len(parts) > 2 else '',
                'scale': 1.0,
                'type': 'digital',
                'normal_state': int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else None,
                'mask': int(parts[4]) if len(parts) > 4 and parts[4].strip().isdigit() else None
            })

    # The line after the last channel is the number of samples (can be ignored or stored)
    # The next line is the number of sampling rates
    nrates = int(lines[2 + total_channels + 1])
    metadata['nrates'] = nrates

    # The next nrates lines are the sampling rates
    for i in range(nrates):
        parts = lines[2 + total_channels + 2 + i].split(',')
        if len(parts) == 2:
            sampling_rates.append((float(parts[0]), int(parts[1])))
    metadata['sampling_rates'] = sampling_rates

    # Parse start time (COMTRADE: date,time)
    try:
        start_date = lines[2 + total_channels + 2 + nrates].strip()
        start_time = lines[2 + total_channels + 3 + nrates].strip()
        dt_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S.%f")
        except ValueError:
            start_datetime = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
        metadata['start_datetime'] = start_datetime
    except Exception:
        metadata['start_datetime'] = None

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

        # Analog scaling with a, b, and primary/secondary if needed
        analog_scaled = []
        for v, ch in zip(analogs, channels[:n_analog]):
            val = ch.get('a', ch.get('scale', 1.0)) * v + ch.get('b', 0.0)
            analog_scaled.append(val)

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
