#!/usr/bin/env python3
"""
MS4GC - MakeSignal4GoConfigure
Version 1.06

Generate time/voltage point pairs for custom signal definitions.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence


PROGRAM_NAME = "MS4GC"
PROGRAM_LONG_NAME = "MakeSignal4GoConfigure"
VERSION = "1.06"
DEFAULT_FILE = "MS4GCdefault.json"
VALID_LANGUAGES = ("en", "de")
VALID_EDGEPOS = ("start", "center", "end")
EPS = 1e-12

BUILTIN_DEFAULTS = {
    "language": "en",
    "timebase_ms": 1.0,
    "interval_ms": 20.0,
    "phase_ms": 0.0,
    "invert": False,
    "ramp": "1%",
    "edgepos": "center",
    "high_v": 5.0,
    "low_v": 0.0,
}

TEXT = {
    "en": {
        "description": f"{PROGRAM_LONG_NAME} Version {VERSION}: generate time/voltage point pairs for signal generators and custom signal import workflows.",
        "version_help": "show program version and exit",
        "bitsignal_help": "binary sequence made of zeros and ones, for example 0011010",
        "timebase_help": "timebase for bit signals and percentage ramps, default 1ms. Examples: 1ms, 10us, 0.5s",
        "interval_help": "output interval for bit signals, default 20ms",
        "phase_help": "shift the whole signal in time. Positive values delay the signal, negative values advance it. Examples: -2ms, 0.5ms",
        "invert_help": "invert the logical signal states before transition generation. Timing remains unchanged; high and low states are exchanged.",
        "noinvert_help": "disable signal inversion, including an inversion stored in MS4GCdefault.json",
        "clock_help": "generate a low/high clock signal. LOW_TIME and HIGH_TIME are times; CLOCKS is the number of low-high cycles. Example: -clock 0.48 0.51 20",
        "edgepos_help": "position of the ideal switching time relative to the transition: start, center, or end. Default: center",
        "ramp_help": "rise/fall ramp, default 1%% of timebase. Examples: 1%%, 0.01ms, 10us",
        "rise_help": "individual rising time. Overrides ramp for rising edges.",
        "fall_help": "individual falling time. Overrides ramp for falling edges.",
        "signal_help": "set high and low level, for example -signal 5 0 or -signal 2.5 -2.5",
        "high_help": "set only the high level in volts",
        "low_help": "set only the low level in volts",
        "language_help": "output/help language. Default is en; can be stored in MS4GCdefault.json.",
        "show_help": "show current default values",
        "save_help": "save current values as defaults in MS4GCdefault.json",
        "file_help": "output filename. .dat is appended automatically if missing.",
        "noheader_help": "write only point pairs without the parameter header",
        "defaults_saved": "Defaults saved to {file}",
        "current_defaults": "Current default values:",
        "read_warning": "Warning: Could not read {file}: {error}",
        "missing_bitsignal": "missing required signal argument, for example 0011010",
        "invalid_time": "Invalid time value: {value}",
        "invalid_signal": "The signal may only contain zeros and ones.",
        "empty_signal": "No bit sequence was specified.",
        "timebase_positive": "timebase must be greater than 0.",
        "interval_positive": "interval must be greater than 0.",
        "rise_fall_nonnegative": "rise and fall must not be negative.",
        "rise_too_large": "rise must not be greater than timebase.",
        "fall_too_large": "fall must not be greater than timebase.",
        "interval_too_short": "interval is too short. The signal requires at least {duration} ms.",
        "low_time_positive": "low-time must be greater than 0.",
        "high_time_positive": "high-time must be greater than 0.",
        "clocks_positive": "clocks must be greater than 0.",
        "clock_integer": "CLOCKS must be an integer.",
        "rise_low_too_large": "rise must not be greater than low-time.",
        "fall_high_too_large": "fall must not be greater than high-time.",
        "fall_low_too_large": "fall must not be greater than low-time when the clock is inverted.",
        "rise_high_too_large": "rise must not be greater than high-time when the clock is inverted.",
        "file_exists": "File already exists: {file}",
        "would_generate": "The file would be generated with these parameters:",
        "overwrite": "Overwrite file? [y/N]: ",
        "aborted": "Aborted. File was not overwritten.",
        "file_written": "File written: {file}",
        "error": "Error: {error}",
    },
    "de": {
        "description": f"{PROGRAM_LONG_NAME} Version {VERSION}: erzeugt Zeit-Spannungs-Wertepaare für Signalgeneratoren und Custom-Signal-Importe.",
        "version_help": "zeigt die Versionsnummer an und beendet das Programm",
        "bitsignal_help": "Bitfolge aus Nullen und Einsen, z. B. 0011010",
        "timebase_help": "Zeitbasis für Bitfolgen und Prozent-Rampen, default 1ms. Beispiele: 1ms, 10us, 0.5s",
        "interval_help": "Ausgabeintervall für Bitfolgen, default 20ms",
        "phase_help": "verschiebt das gesamte Signal zeitlich. Positive Werte verzögern, negative Werte ziehen vor. Beispiele: -2ms, 0.5ms",
        "invert_help": "invertiert die logischen Signalzustände vor der Flankenerzeugung. Der zeitliche Verlauf bleibt unverändert; High und Low werden vertauscht.",
        "noinvert_help": "deaktiviert die Signalinvertierung, auch wenn sie in MS4GCdefault.json gespeichert ist",
        "clock_help": "erzeugt ein Low-/High-Taktsignal. LOW_TIME und HIGH_TIME sind Zeiten; CLOCKS ist die Anzahl der Low-High-Zyklen. Beispiel: -clock 0.48 0.51 20",
        "edgepos_help": "Position des idealen Umschaltzeitpunkts relativ zur Flanke: start, center oder end. Default: center",
        "ramp_help": "Rise/Fall-Rampe, default 1%% von timebase. Beispiele: 1%%, 0.01ms, 10us",
        "rise_help": "individuelle Rising-Time. Überschreibt ramp für steigende Flanken.",
        "fall_help": "individuelle Falling-Time. Überschreibt ramp für fallende Flanken.",
        "signal_help": "setzt High- und Lowlevel, z. B. -signal 5 0 oder -signal 2.5 -2.5",
        "high_help": "setzt nur den Highlevel in Volt",
        "low_help": "setzt nur den Lowlevel in Volt",
        "language_help": "Sprache für Ausgabe/Hilfe. Default ist en; kann in MS4GCdefault.json gespeichert werden.",
        "show_help": "zeigt die aktuellen Defaultwerte an",
        "save_help": "speichert die aktuellen Werte als Default in MS4GCdefault.json",
        "file_help": "Dateiname für Ausgabe. .dat wird automatisch ergänzt.",
        "noheader_help": "schreibt nur Wertepaare ohne Parameter-Header",
        "defaults_saved": "Defaults gespeichert in {file}",
        "current_defaults": "Aktuelle Defaultwerte:",
        "read_warning": "Warnung: Konnte {file} nicht lesen: {error}",
        "missing_bitsignal": "Das nicht-optionale Argument signal fehlt, z. B. 0011010",
        "invalid_time": "Ungültige Zeitangabe: {value}",
        "invalid_signal": "Das Signal darf nur aus Nullen und Einsen bestehen.",
        "empty_signal": "Es wurde keine Bitfolge angegeben.",
        "timebase_positive": "timebase muss größer als 0 sein.",
        "interval_positive": "interval muss größer als 0 sein.",
        "rise_fall_nonnegative": "rise und fall dürfen nicht negativ sein.",
        "rise_too_large": "rise darf nicht größer als timebase sein.",
        "fall_too_large": "fall darf nicht größer als timebase sein.",
        "interval_too_short": "interval ist zu kurz. Signal benötigt mindestens {duration} ms.",
        "low_time_positive": "low-time muss größer als 0 sein.",
        "high_time_positive": "high-time muss größer als 0 sein.",
        "clocks_positive": "clocks muss größer als 0 sein.",
        "clock_integer": "CLOCKS muss eine ganze Zahl sein.",
        "rise_low_too_large": "rise darf nicht größer als low-time sein.",
        "fall_high_too_large": "fall darf nicht größer als high-time sein.",
        "fall_low_too_large": "fall darf bei invertiertem Takt nicht größer als low-time sein.",
        "rise_high_too_large": "rise darf bei invertiertem Takt nicht größer als high-time sein.",
        "file_exists": "Datei existiert bereits: {file}",
        "would_generate": "Die Datei würde mit folgenden Parametern erzeugt:",
        "overwrite": "Datei überschreiben? [j/N]: ",
        "aborted": "Abgebrochen. Datei wurde nicht überschrieben.",
        "file_written": "Datei geschrieben: {file}",
        "error": "Fehler: {error}",
    },
}


def tr(language: str, key: str, **kwargs) -> str:
    text = TEXT.get(language, TEXT["en"]).get(key, TEXT["en"][key])
    return text.format(**kwargs)


def normalize_language(value: object) -> str:
    lang = str(value).strip().lower()
    if lang in VALID_LANGUAGES:
        return lang
    return "en"


def normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "ja"}
    return bool(value)


def parse_time_to_ms(value: str) -> float:
    value_string = str(value).strip().lower()
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*(ns|us|µs|ms|s)?", value_string)
    if not match:
        raise argparse.ArgumentTypeError(tr("en", "invalid_time", value=value))

    number = float(match.group(1))
    unit = match.group(2) or "ms"
    factor = {
        "ns": 1e-6,
        "us": 1e-3,
        "µs": 1e-3,
        "ms": 1.0,
        "s": 1000.0,
    }[unit]
    return number * factor


def parse_ramp_to_ms(value: str, timebase_ms: float) -> float:
    value_string = str(value).strip().lower()
    if value_string.endswith("%"):
        return timebase_ms * float(value_string[:-1]) / 100.0
    return parse_time_to_ms(value_string)


def format_number(value: float) -> str:
    if abs(value) < EPS:
        value = 0.0
    text = f"{value:.12g}"
    if "e" not in text.lower() and "." not in text:
        text += ".0"
    return text


def normalize_defaults(data: dict) -> dict:
    defaults = dict(BUILTIN_DEFAULTS)

    if "clock_ms" in data and "timebase_ms" not in data:
        data["timebase_ms"] = data["clock_ms"]

    for key in ("timebase_ms", "interval_ms", "phase_ms", "high_v", "low_v"):
        if key in data:
            defaults[key] = data[key]

    if "invert" in data:
        defaults["invert"] = normalize_bool(data["invert"])

    if "language" in data:
        defaults["language"] = normalize_language(data["language"])

    if "edgepos" in data:
        edgepos = str(data["edgepos"]).lower()
        if edgepos in VALID_EDGEPOS:
            defaults["edgepos"] = edgepos

    has_ramp = "ramp" in data
    has_rise = "rise_ms" in data and data["rise_ms"] is not None
    has_fall = "fall_ms" in data and data["fall_ms"] is not None

    if has_rise and has_fall:
        rise_ms = float(data["rise_ms"])
        fall_ms = float(data["fall_ms"])
        if abs(rise_ms - fall_ms) < EPS:
            defaults["ramp"] = data["ramp"] if has_ramp else f"{format_number(rise_ms)}ms"
        else:
            defaults.pop("ramp", None)
            defaults["rise_ms"] = rise_ms
            defaults["fall_ms"] = fall_ms
    elif has_ramp:
        defaults["ramp"] = data["ramp"]

    return defaults


def load_defaults() -> dict:
    path = Path(DEFAULT_FILE)
    if not path.exists():
        return normalize_defaults({})
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("JSON root must be an object")
        return normalize_defaults(loaded)
    except Exception as exc:
        print(tr("en", "read_warning", file=DEFAULT_FILE, error=exc), file=sys.stderr)
        return normalize_defaults({})


def preparse_language(argv: Sequence[str], defaults: dict) -> str:
    language = normalize_language(defaults.get("language", "en"))
    for index, arg in enumerate(argv):
        if arg == "-language" and index + 1 < len(argv):
            return normalize_language(argv[index + 1])
        if arg.startswith("-language="):
            return normalize_language(arg.split("=", 1)[1])
    return language


def ramp_mode_from_defaults(defaults: dict) -> str:
    if "rise_ms" in defaults and "fall_ms" in defaults:
        return "risefall"
    return "ramp"


def resolve_rise_fall(args: argparse.Namespace, defaults: dict, timebase_ms: float) -> tuple[float, float, str | None]:
    if args.ramp is not None:
        ramp_raw = args.ramp
        ramp_ms = parse_ramp_to_ms(ramp_raw, timebase_ms)
        rise_ms = fall_ms = ramp_ms
        ramp_source = ramp_raw
    elif ramp_mode_from_defaults(defaults) == "risefall":
        rise_ms = float(defaults["rise_ms"])
        fall_ms = float(defaults["fall_ms"])
        ramp_source = None
    else:
        ramp_source = str(defaults["ramp"])
        ramp_ms = parse_ramp_to_ms(ramp_source, timebase_ms)
        rise_ms = fall_ms = ramp_ms

    if args.rise is not None:
        rise_ms = args.rise
    if args.fall is not None:
        fall_ms = args.fall
    return rise_ms, fall_ms, ramp_source


def edge_times(clock_time_ms: float, ramp_time_ms: float, edgepos: str) -> tuple[float, float]:
    if edgepos == "start":
        return clock_time_ms, clock_time_ms + ramp_time_ms
    if edgepos == "center":
        return clock_time_ms - ramp_time_ms / 2.0, clock_time_ms + ramp_time_ms / 2.0
    if edgepos == "end":
        return clock_time_ms - ramp_time_ms, clock_time_ms
    raise ValueError(f"Invalid edgepos: {edgepos}")


def validate_bitsignal(bitsignal: str, language: str) -> None:
    if not bitsignal:
        raise ValueError(tr(language, "empty_signal"))
    if not re.fullmatch(r"[01]+", bitsignal):
        raise ValueError(tr(language, "invalid_signal"))


def check_common_signal_values(timebase_ms: float, rise_ms: float, fall_ms: float, language: str) -> None:
    if timebase_ms <= 0:
        raise ValueError(tr(language, "timebase_positive"))
    if rise_ms < 0 or fall_ms < 0:
        raise ValueError(tr(language, "rise_fall_nonnegative"))
    if rise_ms > timebase_ms:
        raise ValueError(tr(language, "rise_too_large"))
    if fall_ms > timebase_ms:
        raise ValueError(tr(language, "fall_too_large"))


def generate_raw_bit_signal_pairs(
    bitsignal: str,
    timebase_ms: float,
    interval_ms: float,
    rise_ms: float,
    fall_ms: float,
    edgepos: str,
    high_v: float,
    low_v: float,
    invert: bool = False,
    language: str = "en",
) -> list[tuple[float, float]]:
    validate_bitsignal(bitsignal, language)
    if invert:
        bitsignal = "".join("1" if bit == "0" else "0" for bit in bitsignal)
    check_common_signal_values(timebase_ms, rise_ms, fall_ms, language)
    if interval_ms <= 0:
        raise ValueError(tr(language, "interval_positive"))
    if edgepos not in VALID_EDGEPOS:
        raise ValueError(f"edgepos must be one of: {', '.join(VALID_EDGEPOS)}")

    signal_duration_ms = len(bitsignal) * timebase_ms
    if interval_ms < signal_duration_ms:
        raise ValueError(tr(language, "interval_too_short", duration=format_number(signal_duration_ms)))

    def level(bit: str) -> float:
        return high_v if bit == "1" else low_v

    pairs: list[tuple[float, float]] = [(0.0, level(bitsignal[0]))]
    previous_bit = bitsignal[0]
    previous_level = level(previous_bit)

    for index in range(1, len(bitsignal)):
        current_bit = bitsignal[index]
        current_level = level(current_bit)
        if current_bit != previous_bit:
            clock_time = index * timebase_ms
            ramp_time = rise_ms if current_bit == "1" else fall_ms
            start_time, end_time = edge_times(clock_time, ramp_time, edgepos)
            pairs.append((start_time, previous_level))
            pairs.append((end_time, current_level))
        previous_bit = current_bit
        previous_level = current_level

    pairs.append((interval_ms, level(bitsignal[-1])))
    return pairs


def generate_raw_clock_signal_pairs(
    low_time_ms: float,
    high_time_ms: float,
    clocks: int,
    rise_ms: float,
    fall_ms: float,
    edgepos: str,
    high_v: float,
    low_v: float,
    invert: bool = False,
    language: str = "en",
) -> list[tuple[float, float]]:
    if low_time_ms <= 0:
        raise ValueError(tr(language, "low_time_positive"))
    if high_time_ms <= 0:
        raise ValueError(tr(language, "high_time_positive"))
    if clocks <= 0:
        raise ValueError(tr(language, "clocks_positive"))
    if rise_ms < 0 or fall_ms < 0:
        raise ValueError(tr(language, "rise_fall_nonnegative"))
    if invert:
        if fall_ms > low_time_ms:
            raise ValueError(tr(language, "fall_low_too_large"))
        if rise_ms > high_time_ms:
            raise ValueError(tr(language, "rise_high_too_large"))
    else:
        if rise_ms > low_time_ms:
            raise ValueError(tr(language, "rise_low_too_large"))
        if fall_ms > high_time_ms:
            raise ValueError(tr(language, "fall_high_too_large"))
    if edgepos not in VALID_EDGEPOS:
        raise ValueError(f"edgepos must be one of: {', '.join(VALID_EDGEPOS)}")

    initial_level = high_v if invert else low_v
    second_level = low_v if invert else high_v
    first_ramp_ms = fall_ms if invert else rise_ms
    second_ramp_ms = rise_ms if invert else fall_ms

    pairs: list[tuple[float, float]] = [(0.0, initial_level)]
    clock_time = 0.0
    for _ in range(clocks):
        clock_time += low_time_ms
        start_time, end_time = edge_times(clock_time, first_ramp_ms, edgepos)
        pairs.append((start_time, initial_level))
        pairs.append((end_time, second_level))

        clock_time += high_time_ms
        start_time, end_time = edge_times(clock_time, second_ramp_ms, edgepos)
        pairs.append((start_time, second_level))
        pairs.append((end_time, initial_level))

    return pairs


def value_at_raw_time(raw_pairs: Sequence[tuple[float, float]], time_ms: float) -> float:
    """Return the signal value at a raw, unshifted time using linear interpolation."""
    if not raw_pairs:
        raise ValueError("no raw signal points")

    pairs = sorted(raw_pairs, key=lambda item: item[0])
    times = [p[0] for p in pairs]

    if time_ms <= times[0] + EPS:
        # If multiple points exist at the first timestamp, use the last one at this exact time.
        value = pairs[0][1]
        for t, v in pairs:
            if abs(t - times[0]) <= EPS:
                value = v
            else:
                break
        return value

    if time_ms >= times[-1] - EPS:
        return pairs[-1][1]

    # Exact timestamp: use the last value at that time. This handles zero-length ramps.
    exact_value = None
    for t, v in pairs:
        if abs(t - time_ms) <= EPS:
            exact_value = v
        elif t > time_ms + EPS and exact_value is not None:
            break
    if exact_value is not None:
        return exact_value

    insert_index = bisect.bisect_right(times, time_ms)
    left_index = insert_index - 1
    right_index = insert_index

    while right_index < len(pairs) and abs(pairs[right_index][0] - pairs[left_index][0]) <= EPS:
        right_index += 1

    if right_index >= len(pairs):
        return pairs[left_index][1]

    t0, v0 = pairs[left_index]
    t1, v1 = pairs[right_index]
    if abs(t1 - t0) <= EPS:
        return v1

    fraction = (time_ms - t0) / (t1 - t0)
    return v0 + fraction * (v1 - v0)


def unique_sorted_times(times: Iterable[float]) -> list[float]:
    result: list[float] = []
    for time_value in sorted(times):
        if not result or abs(time_value - result[-1]) > EPS:
            result.append(0.0 if abs(time_value) < EPS else time_value)
    return result


def apply_phase_and_clip(
    raw_pairs: Sequence[tuple[float, float]],
    phase_ms: float,
    window_end_ms: float,
) -> list[tuple[float, float]]:
    """
    Shift all raw point times by phase and clip to [0, window_end_ms].

    Points at the clipping boundaries are interpolated. This keeps partially visible
    linear ramps mathematically correct.
    """
    if window_end_ms < 0:
        raise ValueError("window end must not be negative")

    candidate_times = {0.0, window_end_ms}
    for raw_time, _ in raw_pairs:
        shifted_time = raw_time + phase_ms
        if -EPS <= shifted_time <= window_end_ms + EPS:
            candidate_times.add(min(max(shifted_time, 0.0), window_end_ms))

    clipped_pairs = []
    for shifted_time in unique_sorted_times(candidate_times):
        raw_time = shifted_time - phase_ms
        clipped_pairs.append((shifted_time, value_at_raw_time(raw_pairs, raw_time)))

    return clipped_pairs


def generate_bit_signal_pairs(*args, phase_ms: float = 0.0, **kwargs) -> list[tuple[float, float]]:
    raw_pairs = generate_raw_bit_signal_pairs(*args, **kwargs)
    interval_ms = kwargs.get("interval_ms")
    if interval_ms is None and len(args) >= 3:
        interval_ms = args[2]
    return apply_phase_and_clip(raw_pairs, phase_ms, float(interval_ms))


def generate_clock_signal_pairs(*args, phase_ms: float = 0.0, **kwargs) -> list[tuple[float, float]]:
    raw_pairs = generate_raw_clock_signal_pairs(*args, **kwargs)
    window_end_ms = raw_pairs[-1][0]
    return apply_phase_and_clip(raw_pairs, phase_ms, window_end_ms)


def make_output_filename(filename: str) -> str:
    if not filename.lower().endswith(".dat"):
        filename += ".dat"
    return filename


def build_command_line(argv: Sequence[str]) -> str:
    if argv:
        return " ".join([PROGRAM_NAME] + [shlex.quote(arg) for arg in argv])
    return PROGRAM_NAME


def build_header(config: dict, mode: str) -> list[str]:
    lines = [
        f"{PROGRAM_NAME} Version {VERSION}",
        f"command = {config['command']}",
        f"language = {config['language']}",
        f"timebase = {format_number(config['timebase_ms'])} [ms]",
        f"phase = {format_number(config['phase_ms'])} [ms]",
        f"invert = {str(config['invert']).lower()}",
        f"edgepos = {config['edgepos']}",
    ]
    if mode == "bitsignal":
        lines.append(f"interval = {format_number(config['interval_ms'])} [ms]")
    if abs(config["rise_ms"] - config["fall_ms"]) < EPS:
        lines.append(f"ramp = {config['ramp_raw']}" if config.get("ramp_raw") is not None else f"ramp = {format_number(config['rise_ms'])} [ms]")
    else:
        lines.append(f"rise = {format_number(config['rise_ms'])} [ms]")
        lines.append(f"fall = {format_number(config['fall_ms'])} [ms]")
    lines.append(f"high = {format_number(config['high_v'])} [V]")
    lines.append(f"low = {format_number(config['low_v'])} [V]")
    if mode == "clock":
        lines.append(f"clock-low-time = {format_number(config['clock_low_time_ms'])} [ms]")
        lines.append(f"clock-high-time = {format_number(config['clock_high_time_ms'])} [ms]")
        lines.append(f"clocks = {config['clock_count']}")
    return lines


def write_output(config: dict, pairs: Sequence[tuple[float, float]], filename: str | None, mode: str, header: bool, language: str) -> None:
    lines: list[str] = []
    if header:
        lines.extend(build_header(config, mode))
    for time_ms, voltage_v in pairs:
        lines.append(f"{format_number(time_ms)} {format_number(voltage_v)}")
    output_text = "\n".join(lines) + "\n"

    if filename is None:
        print(output_text, end="")
        return

    output_filename = make_output_filename(filename)
    if os.path.exists(output_filename):
        print(tr(language, "file_exists", file=output_filename))
        print()
        print(tr(language, "would_generate"))
        for line in build_header(config, mode):
            print(line)
        answer = input(tr(language, "overwrite")).strip().lower()
        yes_answers = ("y", "yes") if language == "en" else ("j", "ja", "y", "yes")
        if answer not in yes_answers:
            print(tr(language, "aborted"))
            return

    with open(output_filename, "w", encoding="utf-8") as handle:
        handle.write(output_text)
    print(tr(language, "file_written", file=output_filename))


def save_defaults(config: dict, language: str) -> None:
    data = {
        "version": VERSION,
        "language": config["language"],
        "timebase_ms": config["timebase_ms"],
        "interval_ms": config["interval_ms"],
        "phase_ms": config["phase_ms"],
        "invert": config["invert"],
        "edgepos": config["edgepos"],
        "high_v": config["high_v"],
        "low_v": config["low_v"],
    }

    if abs(config["rise_ms"] - config["fall_ms"]) < EPS:
        data["ramp"] = config["ramp_raw"] if config.get("ramp_raw") is not None else f"{format_number(config['rise_ms'])}ms"
    else:
        data["rise_ms"] = config["rise_ms"]
        data["fall_ms"] = config["fall_ms"]

    with open(DEFAULT_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4)
    print(tr(language, "defaults_saved", file=DEFAULT_FILE))


def show_defaults(defaults: dict, language: str) -> None:
    print(f"{PROGRAM_NAME} - {PROGRAM_LONG_NAME}")
    print(f"Version {VERSION}")
    print()
    print(tr(language, "current_defaults"))
    print(f"language = {defaults['language']}")
    print(f"timebase = {format_number(float(defaults['timebase_ms']))} ms")
    print(f"interval = {format_number(float(defaults['interval_ms']))} ms")
    print(f"phase = {format_number(float(defaults['phase_ms']))} ms")
    print(f"invert = {str(bool(defaults['invert'])).lower()}")
    print(f"edgepos = {defaults['edgepos']}")
    if ramp_mode_from_defaults(defaults) == "risefall":
        print(f"rise = {format_number(float(defaults['rise_ms']))} ms")
        print(f"fall = {format_number(float(defaults['fall_ms']))} ms")
    else:
        print(f"ramp = {defaults['ramp']}")
    print(f"high = {format_number(float(defaults['high_v']))} V")
    print(f"low = {format_number(float(defaults['low_v']))} V")


def create_argument_parser(language: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=tr(language, "description"))
    parser.add_argument("-version", action="version", version=f"{PROGRAM_NAME} Version {VERSION}", help=tr(language, "version_help"))
    parser.add_argument("bitsignal", nargs="?", help=tr(language, "bitsignal_help"))
    parser.add_argument("-timebase", type=parse_time_to_ms, help=tr(language, "timebase_help"))
    parser.add_argument("-interval", type=parse_time_to_ms, help=tr(language, "interval_help"))
    parser.add_argument("-phase", type=parse_time_to_ms, help=tr(language, "phase_help"))
    invert_group = parser.add_mutually_exclusive_group()
    invert_group.add_argument("-invert", dest="invert", action="store_true", default=None, help=tr(language, "invert_help"))
    invert_group.add_argument("-noinvert", dest="invert", action="store_false", help=tr(language, "noinvert_help"))
    parser.add_argument("-clock", nargs=3, metavar=("LOW_TIME", "HIGH_TIME", "CLOCKS"), help=tr(language, "clock_help"))
    parser.add_argument("-edgepos", choices=VALID_EDGEPOS, help=tr(language, "edgepos_help"))
    parser.add_argument("-ramp", help=tr(language, "ramp_help"))
    parser.add_argument("-rise", type=parse_time_to_ms, help=tr(language, "rise_help"))
    parser.add_argument("-fall", type=parse_time_to_ms, help=tr(language, "fall_help"))
    parser.add_argument("-signal", nargs=2, metavar=("HIGH", "LOW"), type=float, help=tr(language, "signal_help"))
    parser.add_argument("-high", type=float, help=tr(language, "high_help"))
    parser.add_argument("-low", type=float, help=tr(language, "low_help"))
    parser.add_argument("-language", choices=VALID_LANGUAGES, help=tr(language, "language_help"))
    parser.add_argument("-show", action="store_true", help=tr(language, "show_help"))
    parser.add_argument("-save", action="store_true", help=tr(language, "save_help"))
    parser.add_argument("-file", help=tr(language, "file_help"))
    parser.add_argument("-noheader", action="store_true", help=tr(language, "noheader_help"))
    return parser


def build_config(args: argparse.Namespace, defaults: dict, language: str, argv: Sequence[str]) -> dict:
    timebase_ms = args.timebase if args.timebase is not None else float(defaults["timebase_ms"])
    interval_ms = args.interval if args.interval is not None else float(defaults["interval_ms"])
    phase_ms = args.phase if args.phase is not None else float(defaults["phase_ms"])
    invert = args.invert if args.invert is not None else bool(defaults["invert"])
    edgepos = args.edgepos if args.edgepos is not None else defaults["edgepos"]
    output_language = args.language if args.language is not None else language

    rise_ms, fall_ms, ramp_source = resolve_rise_fall(args, defaults, timebase_ms)

    high_v = float(defaults["high_v"])
    low_v = float(defaults["low_v"])
    if args.signal is not None:
        high_v, low_v = args.signal[0], args.signal[1]
    if args.high is not None:
        high_v = args.high
    if args.low is not None:
        low_v = args.low

    return {
        "command": build_command_line(argv),
        "language": output_language,
        "timebase_ms": timebase_ms,
        "interval_ms": interval_ms,
        "phase_ms": phase_ms,
        "invert": invert,
        "edgepos": edgepos,
        "ramp_raw": ramp_source,
        "rise_ms": rise_ms,
        "fall_ms": fall_ms,
        "high_v": high_v,
        "low_v": low_v,
    }


def normalize_argv_for_negative_phase(argv: Sequence[str]) -> list[str]:
    """Allow command lines such as -phase -2ms.

    argparse normally treats values starting with '-' as options. For phase,
    negative values are valid and important, so we rewrite '-phase -2ms' to
    '-phase=-2ms' before parsing.
    """
    result: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "-phase" and index + 1 < len(argv):
            next_arg = argv[index + 1]
            if re.fullmatch(r"-\d+(?:\.\d+)?\s*(?:ns|us|µs|ms|s)?", next_arg.strip().lower()):
                result.append(f"-phase={next_arg}")
                index += 2
                continue
        result.append(argv[index])
        index += 1
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argv = normalize_argv_for_negative_phase(list(sys.argv[1:] if argv is None else argv))
    defaults = load_defaults()
    language = preparse_language(argv, defaults)
    parser = create_argument_parser(language)
    args = parser.parse_args(argv)
    language = args.language if args.language is not None else language

    if args.show:
        show_defaults(defaults, language)
        if args.bitsignal is None and args.clock is None and not args.save:
            return 0

    config = build_config(args, defaults, language, argv)

    if args.save:
        save_defaults(config, language)

    try:
        if args.clock is not None:
            low_time_ms = parse_time_to_ms(args.clock[0])
            high_time_ms = parse_time_to_ms(args.clock[1])
            try:
                clock_count = int(args.clock[2])
            except ValueError:
                raise ValueError(tr(language, "clock_integer"))

            config["clock_low_time_ms"] = low_time_ms
            config["clock_high_time_ms"] = high_time_ms
            config["clock_count"] = clock_count
            pairs = generate_clock_signal_pairs(
                low_time_ms=low_time_ms,
                high_time_ms=high_time_ms,
                clocks=clock_count,
                rise_ms=config["rise_ms"],
                fall_ms=config["fall_ms"],
                edgepos=config["edgepos"],
                high_v=config["high_v"],
                low_v=config["low_v"],
                invert=config["invert"],
                language=language,
                phase_ms=config["phase_ms"],
            )
            write_output(config, pairs, args.file, mode="clock", header=not args.noheader, language=language)
            return 0

        if args.bitsignal is None:
            if args.save:
                return 0
            parser.error(tr(language, "missing_bitsignal"))

        pairs = generate_bit_signal_pairs(
            bitsignal=args.bitsignal,
            timebase_ms=config["timebase_ms"],
            interval_ms=config["interval_ms"],
            rise_ms=config["rise_ms"],
            fall_ms=config["fall_ms"],
            edgepos=config["edgepos"],
            high_v=config["high_v"],
            low_v=config["low_v"],
            invert=config["invert"],
            language=language,
            phase_ms=config["phase_ms"],
        )
        write_output(config, pairs, args.file, mode="bitsignal", header=not args.noheader, language=language)
    except Exception as exc:
        print(tr(language, "error", error=exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
