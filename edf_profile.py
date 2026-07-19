#!/usr/bin/env python3
"""Read-only EDF/EDF+ profiler using only the Python standard library.

The script intentionally never emits the EDF patient or recording text fields.
"""

from __future__ import annotations

import argparse
from array import array
from collections import Counter
import json
import math
import mmap
from pathlib import Path
import re
from statistics import median
import sys


FIELD_SPECS = [
    ("label", 16),
    ("transducer", 80),
    ("unit", 8),
    ("physical_min", 8),
    ("physical_max", 8),
    ("digital_min", 8),
    ("digital_max", 8),
    ("prefilter", 80),
    ("samples_per_record", 8),
    ("reserved", 32),
]


def decode(raw: bytes) -> str:
    return raw.decode("ascii", "replace").strip()


def read_header(path: Path) -> dict:
    with path.open("rb") as handle:
        fixed = handle.read(256)
        if len(fixed) != 256:
            raise ValueError("File is too small to contain an EDF header")
        header_bytes = int(decode(fixed[184:192]))
        n_records = int(decode(fixed[236:244]))
        record_duration = float(decode(fixed[244:252]))
        n_signals = int(decode(fixed[252:256]))
        signal_header = handle.read(header_bytes - 256)

    fields: dict[str, list[str]] = {}
    offset = 0
    for name, width in FIELD_SPECS:
        fields[name] = [
            decode(signal_header[offset + i * width : offset + (i + 1) * width])
            for i in range(n_signals)
        ]
        offset += width * n_signals

    samples_per_record = [int(value) for value in fields["samples_per_record"]]
    signal_offsets = []
    cursor = 0
    for samples in samples_per_record:
        signal_offsets.append(cursor)
        cursor += samples * 2

    return {
        "version": decode(fixed[0:8]),
        "patient_field_nonempty": bool(decode(fixed[8:88])),
        "recording_field_nonempty": bool(decode(fixed[88:168])),
        "start_date": decode(fixed[168:176]),
        "start_time": decode(fixed[176:184]),
        "header_bytes": header_bytes,
        "reserved": decode(fixed[192:236]),
        "n_records": n_records,
        "record_duration_seconds": record_duration,
        "n_signals": n_signals,
        "fields": fields,
        "samples_per_record": samples_per_record,
        "signal_offsets": signal_offsets,
        "record_bytes": cursor,
    }


def int16_values(raw: bytes) -> array:
    values = array("h")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()
    return values


def parse_annotations(path: Path, header: dict) -> tuple[list[dict], list[float]]:
    labels = header["fields"]["label"]
    index = labels.index("EDF Annotations")
    events: list[dict] = []
    timekeeping: list[float] = []
    with path.open("rb") as handle:
        for record in range(header["n_records"]):
            start = (
                header["header_bytes"]
                + record * header["record_bytes"]
                + header["signal_offsets"][index]
            )
            handle.seek(start)
            raw = handle.read(header["samples_per_record"][index] * 2)
            for tal in raw.split(b"\x00"):
                if not tal:
                    continue
                parts = tal.split(b"\x14")
                timing = parts[0]
                if b"\x15" in timing:
                    onset_raw, duration_raw = timing.split(b"\x15", 1)
                else:
                    onset_raw, duration_raw = timing, b""
                try:
                    onset = float(onset_raw.decode("ascii"))
                    duration = float(duration_raw.decode("ascii")) if duration_raw else None
                except (UnicodeDecodeError, ValueError):
                    continue
                texts = [part.decode("utf-8", "replace") for part in parts[1:] if part]
                if not texts:
                    timekeeping.append(onset)
                for text in texts:
                    events.append(
                        {
                            "record": record,
                            "onset_seconds": onset,
                            "duration_seconds": duration,
                            "text": text,
                        }
                    )
    return events, timekeeping


def calibration_scale(header: dict, index: int) -> float:
    fields = header["fields"]
    physical_min = float(fields["physical_min"][index])
    physical_max = float(fields["physical_max"][index])
    digital_min = float(fields["digital_min"][index])
    digital_max = float(fields["digital_max"][index])
    return (physical_max - physical_min) / (digital_max - digital_min)


def sample_electrodes(path: Path, header: dict, windows: int, window_seconds: float) -> dict:
    labels = header["fields"]["label"]
    electrode_count = labels.index("EKG")
    records_per_window = max(1, round(window_seconds / header["record_duration_seconds"]))
    if windows == 1:
        starts = [0]
    else:
        starts = [
            round(i * (header["n_records"] - records_per_window) / (windows - 1))
            for i in range(windows)
        ]

    counts = [0] * electrode_count
    sums = [0] * electrode_count
    sums_sq = [0] * electrode_count
    low = [32767] * electrode_count
    high = [-32768] * electrode_count
    clipped = [0] * electrode_count
    repeated = [0] * electrode_count
    pairs = [0] * electrode_count

    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for start_record in starts:
            previous = [None] * electrode_count
            for record in range(start_record, start_record + records_per_window):
                base = header["header_bytes"] + record * header["record_bytes"]
                for index in range(electrode_count):
                    size = header["samples_per_record"][index] * 2
                    values = int16_values(
                        data[
                            base + header["signal_offsets"][index] :
                            base + header["signal_offsets"][index] + size
                        ]
                    )
                    counts[index] += len(values)
                    sums[index] += sum(values)
                    sums_sq[index] += sum(value * value for value in values)
                    low[index] = min(low[index], min(values))
                    high[index] = max(high[index], max(values))
                    clipped[index] += values.count(-32768) + values.count(32767)
                    if previous[index] is not None:
                        repeated[index] += int(values[0] == previous[index])
                        pairs[index] += 1
                    repeated[index] += sum(left == right for left, right in zip(values, values[1:]))
                    pairs[index] += len(values) - 1
                    previous[index] = values[-1]

    rows = []
    for index in range(electrode_count):
        mean = sums[index] / counts[index]
        variance = max(0.0, sums_sq[index] / counts[index] - mean * mean)
        scale = abs(calibration_scale(header, index))
        rows.append(
            {
                "label": labels[index],
                "group": re.sub(r"\d+$", "", labels[index]),
                "sd_uV": math.sqrt(variance) * scale,
                "peak_to_peak_uV": (high[index] - low[index]) * scale,
                "repeat_rate": repeated[index] / pairs[index],
                "clip_rate": clipped[index] / counts[index],
                "digital_min_sampled": low[index],
                "digital_max_sampled": high[index],
                "sample_count": counts[index],
            }
        )

    sd_median = median(row["sd_uV"] for row in rows)
    sd_mad = median(abs(row["sd_uV"] - sd_median) for row in rows)
    threshold = sd_median + 6 * sd_mad
    for row in rows:
        row["above_robust_review_threshold"] = row["sd_uV"] > threshold

    return {
        "contact_count": electrode_count,
        "window_count": windows,
        "window_seconds": records_per_window * header["record_duration_seconds"],
        "sampled_seconds_total": windows * records_per_window * header["record_duration_seconds"],
        "sd_median_uV": sd_median,
        "sd_mad_uV": sd_mad,
        "review_threshold_uV": threshold,
        "channels": rows,
    }


def scan_selected_channels(path: Path, header: dict) -> list[dict]:
    labels = header["fields"]["label"]
    selected = [
        index
        for index, label in enumerate(labels)
        if re.fullmatch(r"C(?:23[5-9]|24\d|25[0-6])", label)
        or label.startswith("DC")
        or label in {"TRIG", "OSAT", "PR", "Pleth"}
    ]
    n = [0] * len(selected)
    zeros = [0] * len(selected)
    clipped = [0] * len(selected)
    low = [32767] * len(selected)
    high = [-32768] * len(selected)
    sums = [0] * len(selected)
    sums_sq = [0] * len(selected)
    repeated = [0] * len(selected)
    pairs = [0] * len(selected)
    previous = [None] * len(selected)

    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for record in range(header["n_records"]):
            base = header["header_bytes"] + record * header["record_bytes"]
            for position, index in enumerate(selected):
                size = header["samples_per_record"][index] * 2
                values = int16_values(
                    data[
                        base + header["signal_offsets"][index] :
                        base + header["signal_offsets"][index] + size
                    ]
                )
                n[position] += len(values)
                zeros[position] += values.count(0)
                clipped[position] += values.count(-32768) + values.count(32767)
                low[position] = min(low[position], min(values))
                high[position] = max(high[position], max(values))
                sums[position] += sum(values)
                sums_sq[position] += sum(value * value for value in values)
                if previous[position] is not None:
                    repeated[position] += int(values[0] == previous[position])
                    pairs[position] += 1
                repeated[position] += sum(
                    left == right for left, right in zip(values, values[1:])
                )
                pairs[position] += len(values) - 1
                previous[position] = values[-1]

    output = []
    for position, index in enumerate(selected):
        mean = sums[position] / n[position]
        variance = max(0.0, sums_sq[position] / n[position] - mean * mean)
        output.append(
            {
                "label": labels[index],
                "unit": header["fields"]["unit"][index],
                "sample_count": n[position],
                "digital_min": low[position],
                "digital_max": high[position],
                "zero_rate": zeros[position] / n[position],
                "clip_rate": clipped[position] / n[position],
                "repeat_rate": repeated[position] / pairs[position],
                "sd_physical": math.sqrt(variance) * abs(calibration_scale(header, index)),
            }
        )
    return output


def trigger_transitions(path: Path, header: dict) -> list[dict]:
    index = header["fields"]["label"].index("TRIG")
    sample_rate = header["samples_per_record"][index] / header["record_duration_seconds"]
    transitions = []
    previous = None
    sample_number = 0
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for record in range(header["n_records"]):
            base = (
                header["header_bytes"]
                + record * header["record_bytes"]
                + header["signal_offsets"][index]
            )
            size = header["samples_per_record"][index] * 2
            values = int16_values(data[base : base + size])
            for value in values:
                if previous is None:
                    previous = value
                elif value != previous:
                    transitions.append(
                        {"relative_seconds": sample_number / sample_rate, "new_code": value}
                    )
                    previous = value
                sample_number += 1
    return transitions


def summarize_trigger(events: list[dict], timekeeping: list[float], transitions: list[dict]) -> dict:
    pattern = re.compile(r"TRIG\[(\d+)\]")
    annotated = []
    for event in events:
        match = pattern.match(event["text"])
        if match:
            annotated.append(
                {"onset_seconds": event["onset_seconds"], "code": int(match.group(1))}
            )
    start_offset = timekeeping[0]
    raw = [
        {
            "onset_seconds": transition["relative_seconds"] + start_offset,
            "code": transition["new_code"],
        }
        for transition in transitions
    ]

    matched_pairs = []
    unmatched_annotations = []
    for annotation in annotated:
        candidates = [
            (
                abs(item["onset_seconds"] - annotation["onset_seconds"]),
                item,
            )
            for item in raw
            if item["code"] == annotation["code"]
        ]
        if not candidates:
            unmatched_annotations.append(annotation)
            continue
        error, item = min(candidates, key=lambda pair: pair[0])
        if error <= 0.010:
            matched_pairs.append(
                {
                    "annotation_seconds": annotation["onset_seconds"],
                    "raw_seconds": item["onset_seconds"],
                    "code": annotation["code"],
                    "absolute_error_ms": error * 1000,
                }
            )
        else:
            unmatched_annotations.append(annotation)

    unmatched_raw = []
    for item in raw:
        if not any(
            annotation["code"] == item["code"]
            and abs(annotation["onset_seconds"] - item["onset_seconds"]) <= 0.010
            for annotation in annotated
        ):
            unmatched_raw.append(item)

    return {
        "annotation_event_count": len(annotated),
        "annotation_code_counts": dict(sorted(Counter(item["code"] for item in annotated).items())),
        "raw_transition_count": len(raw),
        "raw_new_code_counts": dict(sorted(Counter(item["code"] for item in raw).items())),
        "matched_within_10ms": len(matched_pairs),
        "alignment_absolute_error_ms_median": median(
            pair["absolute_error_ms"] for pair in matched_pairs
        ),
        "alignment_absolute_error_ms_max": max(
            pair["absolute_error_ms"] for pair in matched_pairs
        ),
        "unmatched_annotations": unmatched_annotations,
        "unmatched_raw_transitions": unmatched_raw,
        "data_record_start_offset_seconds": start_offset,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("edf", type=Path)
    parser.add_argument("--sample-windows", type=int, default=30)
    parser.add_argument("--window-seconds", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    path = args.edf.resolve()
    header = read_header(path)
    events, timekeeping = parse_annotations(path, header)
    electrode_qc = sample_electrodes(
        path, header, args.sample_windows, args.window_seconds
    )
    selected_channel_qc = scan_selected_channels(path, header)
    transitions = trigger_transitions(path, header)
    trigger_qc = summarize_trigger(events, timekeeping, transitions)

    fields = header["fields"]
    bytes_expected = (
        header["header_bytes"] + header["n_records"] * header["record_bytes"]
    )
    def safe_event_category(text: str) -> str:
        trigger = re.match(r"TRIG\[(\d+)\]", text)
        if trigger:
            return f"TRIG[{int(trigger.group(1)):03d}]"
        if text.startswith("Montage:"):
            return "Montage metadata (text suppressed)"
        return "Other metadata (text suppressed)"

    event_counts = Counter(safe_event_category(event["text"]) for event in events)
    result = {
        "source": path.name,
        "file_size_bytes": path.stat().st_size,
        "file_size_matches_header": path.stat().st_size == bytes_expected,
        "edf": {
            "version": header["version"],
            "variant": header["reserved"],
            "start_date": header["start_date"],
            "start_time": header["start_time"],
            "record_count": header["n_records"],
            "record_duration_seconds": header["record_duration_seconds"],
            "duration_seconds": header["n_records"]
            * header["record_duration_seconds"],
            "signal_count": header["n_signals"],
            "numeric_signal_count": header["n_signals"] - 1,
            "patient_field_nonempty": header["patient_field_nonempty"],
            "recording_field_nonempty": header["recording_field_nonempty"],
            "physical_range_reversed_count": sum(
                float(fields["physical_min"][i]) > float(fields["physical_max"][i])
                for i in range(header["n_signals"])
            ),
            "blank_prefilter_count": sum(not value for value in fields["prefilter"]),
        },
        "sampling_rates_hz": dict(
            sorted(
                Counter(
                    str(
                        header["samples_per_record"][i]
                        / header["record_duration_seconds"]
                    )
                    for i in range(header["n_signals"] - 1)
                ).items()
            )
        ),
        "electrode_qc": electrode_qc,
        "selected_channel_qc": selected_channel_qc,
        "annotations": {
            "event_count_including_metadata": len(events),
            "event_text_counts": dict(event_counts),
            "timekeeping_count": len(timekeeping),
            "timekeeping_first_seconds": timekeeping[0],
            "timekeeping_last_seconds": timekeeping[-1],
        },
        "trigger_qc": trigger_qc,
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
