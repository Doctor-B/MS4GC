#!/usr/bin/env python3
"""
MS4GC - MakeSignal4GoConfigure
Version 1.04

Generate time/voltage point pairs for signal-generator and custom-signal import workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


PROGRAM_NAME = "MS4GC"
PROGRAM_LONG_NAME = "MakeSignal4GoConfigure"
VERSION = "1.04"
DEFAULT_FILE = "MS4GCdefault.json"
VALID_EDGEPOS = ("start", "center", "end")
VALID_LANGUAGES = ("en", "de")

BUILTIN_DEFAULTS: dict[str, Any] = {
    "language": "en",
    "timebase_ms": 1.0,
    "interval_ms": 20.0,
    "ramp": "1%",
    "edgepos": "center",
    "high_v": 5.0,
    "low_v": 0.0,
}

TEXT = {
    "en": {
        "description": f"{PROGRAM_LONG_NAME} Version {VERSION}: generate time/voltage point pairs for custom signal definitions.",
        "version_help": "show the program version",
        "bitsignal_help": "binary signal sequence, for example 0011010",
        "timebase_help": "time base for bit sequences and percentage ramps, default 1ms. Examples: 1ms, 10us, 0.5s",
        "interval_help": "total interval for bit sequences, default 20ms",
        "clock_help": "generate a clock signal. LOW_TIME and HIGH_TIME are times; CLOCKS is the number of low-high cycles. Example: -clock 0.48 0.51 20",
        "edgepos_help": "position of the ideal switching time relative to the edge. start: edge starts at switching time; center: edge center is at switching time; end: edge is complete at switching time. Default: center",
        "ramp_help": "rise/fall ramp, default 1%% of timebase. Examples: 1%, 0.01ms, 10us",
        "rise_help": "individual rising time. Overrides ramp for rising edges.",
        "fall_help": "individual falling time. Overrides ramp for falling edges.",
        "signal_help": "set high and low voltage levels, for example -signal 5 0 or -signal 2.5 -2.5",
        "high_help": "set only the high level in volts",
        "low_help": "set only the low level in volts",
        "language_help": "select output/help language and store it with -save. Default: en; currently supported: en, de",
        "show_help": "show current default values",
        "save_help": f"save current values as defaults in {DEFAULT_FILE}",
        "file_help": "output filename. .dat is appended automatically if missing.",
        "noheader_help": "write point pairs only, without the default parameter header",
        "show_title": "Current default values:",
        "defaults_saved": f"Defaults saved to {DEFAULT_FILE}",
        "exists": "File already exists",
        "would_generate": "The file would be generated with these parameters:",
        "overwrite": "Overwrite file? [y/N]: ",
        "aborted": "Aborted. File was not overwritten.",
        "written": "File written",
        "warning_read": f"Warning: Could not read {DEFAULT_FILE}",
        "invalid_time": "Invalid time value",
        "missing_bitsignal": "missing required signal argument, for example 0011010",
        "err_no_bits": "No bit sequence was specified.",
        "err_bits_chars": "The signal may only contain zeros and ones.",
        "err_timebase": "timebase must be greater than 0.",
        "err_interval": "interval must be greater than 0.",
        "err_risefall_negative": "rise and fall must not be negative.",
        "err_rise_timebase": "rise must not be greater than timebase.",
        "err_fall_timebase": "fall must not be greater than timebase.",
        "err_interval_short": "interval is too short. Signal needs at least",
        "err_low_time": "low-time must be greater than 0.",
        "err_high_time": "high-time must be greater than 0.",
        "err_clocks": "CLOCKS must be greater than 0.",
        "err_clocks_int": "CLOCKS must be an integer.",
        "err_rise_low": "rise must not be greater than low-time.",
        "err_fall_high": "fall must not be greater than high-time.",
        "err_edgepos": "edgepos must be one of",
        "err_negative_edge": "would create a negative edge start time",
        "error": "Error",
    },
    "de": {
        "description": f"{PROGRAM_LONG_NAME} Version {VERSION}: erzeugt Zeit-Spannungs-Wertepaare für benutzerdefinierte Signale.",
        "version_help": "zeigt die Versionsnummer an",
        "bitsignal_help": "Bitfolge aus Nullen und Einsen, z. B. 0011010",
        "timebase_help": "Zeitliche Basis für Bitfolgen und Prozent-Rampen, default 1ms. Beispiele: 1ms, 10us, 0.5s",
        "interval_help": "Gesamtintervall für Bitfolgen, default 20ms",
        "clock_help": "erzeugt ein echtes Taktsignal. LOW_TIME und HIGH_TIME sind Zeiten; CLOCKS ist die Anzahl der Low-High-Zyklen. Beispiel: -clock 0.48 0.51 20",
        "edgepos_help": "Position des idealen Umschaltzeitpunkts relativ zur Flanke. start: Flanke beginnt beim Takt; center: Flankenmitte liegt beim Takt; end: Flanke ist beim Takt abgeschlossen. Default: center",
        "ramp_help": "Rise/Fall-Rampe, default 1%% von timebase. Beispiele: 1%, 0.01ms, 10us",
        "rise_help": "Individuelle Rising-Time. Überschreibt ramp für steigende Flanken.",
        "fall_help": "Individuelle Falling-Time. Überschreibt ramp für fallende Flanken.",
        "signal_help": "Setzt High- und Lowlevel, z. B. -signal 5 0 oder -signal 2.5 -2.5",
        "high_help": "Setzt nur den Highlevel in Volt",
        "low_help": "Setzt nur den Lowlevel in Volt",
        "language_help": "wählt Ausgabe-/Hilfesprache und speichert sie mit -save. Default: en; aktuell unterstützt: en, de",
        "show_help": "zeigt die aktuellen Defaultwerte an",
        "save_help": f"speichert die aktuellen Werte als Default in {DEFAULT_FILE}",
        "file_help": "Dateiname für Ausgabe. .dat wird automatisch ergänzt.",
        "noheader_help": "schreibt nur Wertepaare, ohne den standardmäßigen Parameter-Header",
        "show_title": "Aktuelle Defaultwerte:",
        "defaults_saved": f"Defaults gespeichert in {DEFAULT_FILE}",
        "exists": "Datei existiert bereits",
        "would_generate": "Die Datei würde mit folgenden Parametern erzeugt:",
        "overwrite": "Datei überschreiben? [j/N]: ",
        "aborted": "Abgebrochen. Datei wurde nicht überschrieben.",
        "written": "Datei geschrieben",
        "warning_read": f"Warnung: Konnte {DEFAULT_FILE} nicht lesen",
        "invalid_time": "Ungültige Zeitangabe",
        "missing_bitsignal": "Das nicht-optionale Argument signal fehlt, z. B. 0011010",
        "err_no_bits": "Es wurde keine Bitfolge angegeben.",
        "err_bits_chars": "Das Signal darf nur aus Nullen und Einsen bestehen.",
        "err_timebase": "timebase muss größer als 0 sein.",
        "err_interval": "interval muss größer als 0 sein.",
        "err_risefall_negative": "rise und fall dürfen nicht negativ sein.",
        "err_rise_timebase": "rise darf nicht größer als timebase sein.",
        "err_fall_timebase": "fall darf nicht größer als timebase sein.",
        "err_interval_short": "interval ist zu kurz. Signal benötigt mindestens",
        "err_low_time": "low-time muss größer als 0 sein.",
        "err_high_time": "high-time muss größer als 0 sein.",
        "err_clocks": "CLOCKS muss größer als 0 sein.",
        "err_clocks_int": "CLOCKS muss eine ganze Zahl sein.",
        "err_rise_low": "rise darf nicht größer als low-time sein.",
        "err_fall_high": "fall darf nicht größer als high-time sein.",
        "err_edgepos": "edgepos muss einer dieser Werte sein",
        "err_negative_edge": "würde eine negative Flankenstartzeit erzeugen",
        "error": "Fehler",
    },
}


def tr(lang: str, key: str) -> str:
    return TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def parse_time_to_ms(value: str) -> float:
    value = str(value).strip().lower()
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*(ns|us|µs|ms|s)?", value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid time value: {value}")

    number = float(match.group(1))
    unit = match.group(2) or "ms"
    factor = {"ns": 1e-6, "us": 1e-3, "µs": 1e-3, "ms": 1.0, "s": 1000.0}[unit]
    return number * factor


def parse_ramp_to_ms(value: str, timebase_ms: float) -> float:
    value = str(value).strip().lower()
    if value.endswith("%"):
        return timebase_ms * float(value[:-1]) / 100.0
    return parse_time_to_ms(value)


def format_number(value: float) -> str:
    if abs(value) < 1e-12:
        value = 0.0
    text = f"{value:.12g}"
    if "e" in text.lower():
        return text
    if "." not in text:
        text += ".0"
    return text


def normalize_defaults(data: dict[str, Any]) -> dict[str, Any]:
    defaults = dict(BUILTIN_DEFAULTS)

    if "clock_ms" in data and "timebase_ms" not in data:
        data["timebase_ms"] = data["clock_ms"]

    for key in ("timebase_ms", "interval_ms", "high_v", "low_v"):
        if key in data:
            defaults[key] = data[key]

    if "language" in data:
        language = str(data["language"]).lower()
        if language in VALID_LANGUAGES:
            defaults["language"] = language

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
        if abs(rise_ms - fall_ms) < 1e-12:
            defaults["ramp"] = data["ramp"] if has_ramp else f"{format_number(rise_ms)}ms"
        else:
            defaults.pop("ramp", None)
            defaults["rise_ms"] = rise_ms
            defaults["fall_ms"] = fall_ms
    elif has_ramp:
        defaults["ramp"] = data["ramp"]

    return defaults


def load_defaults() -> dict[str, Any]:
    path = Path(DEFAULT_FILE)
    if not path.exists():
        return normalize_defaults({})
    try:
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("JSON root must be an object.")
        return normalize_defaults(loaded)
    except Exception as exc:
        print(f"Warning: Could not read {DEFAULT_FILE}: {exc}", file=sys.stderr)
        return normalize_defaults({})


def preparse_language(argv: list[str], defaults: dict[str, Any]) -> str:
    language = str(defaults.get("language", "en")).lower()
    for idx, arg in enumerate(argv):
        if arg == "-language" and idx + 1 < len(argv):
            candidate = argv[idx + 1].lower()
            if candidate in VALID_LANGUAGES:
                language = candidate
        elif arg.startswith("-language="):
            candidate = arg.split("=", 1)[1].lower()
            if candidate in VALID_LANGUAGES:
                language = candidate
    return language if language in VALID_LANGUAGES else "en"


def ramp_mode_from_defaults(defaults: dict[str, Any]) -> str:
    if "rise_ms" in defaults and "fall_ms" in defaults:
        return "risefall"
    return "ramp"


def resolve_rise_fall(args: argparse.Namespace, defaults: dict[str, Any], timebase_ms: float):
    if args.ramp is not None:
        ramp_raw = args.ramp
        ramp_ms = parse_ramp_to_ms(ramp_raw, timebase_ms)
        rise_ms = ramp_ms
        fall_ms = ramp_ms
        ramp_source = ramp_raw
    elif ramp_mode_from_defaults(defaults) == "risefall":
        rise_ms = float(defaults["rise_ms"])
        fall_ms = float(defaults["fall_ms"])
        ramp_source = None
    else:
        ramp_source = str(defaults["ramp"])
        ramp_ms = parse_ramp_to_ms(ramp_source, timebase_ms)
        rise_ms = ramp_ms
        fall_ms = ramp_ms

    if args.rise is not None:
        rise_ms = args.rise
    if args.fall is not None:
        fall_ms = args.fall

    return rise_ms, fall_ms, ramp_source


def edge_times(clock_time_ms: float, ramp_time_ms: float, edgepos: str):
    if edgepos == "start":
        return clock_time_ms, clock_time_ms + ramp_time_ms
    if edgepos == "center":
        return clock_time_ms - ramp_time_ms / 2.0, clock_time_ms + ramp_time_ms / 2.0
    if edgepos == "end":
        return clock_time_ms - ramp_time_ms, clock_time_ms
    raise ValueError(f"Invalid edgepos: {edgepos}")


def save_defaults(config: dict[str, Any]) -> None:
    lang = config["language"]
    data: dict[str, Any] = {
        "version": VERSION,
        "language": config["language"],
        "timebase_ms": config["timebase_ms"],
        "interval_ms": config["interval_ms"],
        "edgepos": config["edgepos"],
        "high_v": config["high_v"],
        "low_v": config["low_v"],
    }

    rise_ms = float(config["rise_ms"])
    fall_ms = float(config["fall_ms"])
    if abs(rise_ms - fall_ms) < 1e-12:
        data["ramp"] = config.get("ramp_raw") or f"{format_number(rise_ms)}ms"
    else:
        data["rise_ms"] = rise_ms
        data["fall_ms"] = fall_ms

    with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(tr(lang, "defaults_saved"))


def show_defaults(defaults: dict[str, Any], lang: str) -> None:
    print(f"{PROGRAM_NAME} - {PROGRAM_LONG_NAME}")
    print(f"Version {VERSION}")
    print()
    print(tr(lang, "show_title"))
    print(f"language = {defaults['language']}")
    print(f"timebase = {format_number(float(defaults['timebase_ms']))} ms")
    print(f"interval = {format_number(float(defaults['interval_ms']))} ms")
    print(f"edgepos  = {defaults['edgepos']}")
    if ramp_mode_from_defaults(defaults) == "risefall":
        print(f"rise     = {format_number(float(defaults['rise_ms']))} ms")
        print(f"fall     = {format_number(float(defaults['fall_ms']))} ms")
    else:
        print(f"ramp     = {defaults['ramp']}")
    print(f"high     = {format_number(float(defaults['high_v']))} V")
    print(f"low      = {format_number(float(defaults['low_v']))} V")


def validate_bitsignal(bitsignal: str, lang: str) -> None:
    if not bitsignal:
        raise ValueError(tr(lang, "err_no_bits"))
    if not re.fullmatch(r"[01]+", bitsignal):
        raise ValueError(tr(lang, "err_bits_chars"))


def make_output_filename(filename: str) -> str:
    return filename if filename.lower().endswith(".dat") else filename + ".dat"


def check_non_negative_edge_start(edge_start_ms: float, edgepos: str, lang: str) -> None:
    if edge_start_ms < -1e-12:
        raise ValueError(
            f"edgepos={edgepos} {tr(lang, 'err_negative_edge')}: {format_number(edge_start_ms)} ms"
        )


def generate_bit_signal_pairs(
    bitsignal: str,
    timebase_ms: float,
    interval_ms: float,
    rise_ms: float,
    fall_ms: float,
    edgepos: str,
    high_v: float,
    low_v: float,
    lang: str = "en",
):
    validate_bitsignal(bitsignal, lang)
    if timebase_ms <= 0:
        raise ValueError(tr(lang, "err_timebase"))
    if interval_ms <= 0:
        raise ValueError(tr(lang, "err_interval"))
    if rise_ms < 0 or fall_ms < 0:
        raise ValueError(tr(lang, "err_risefall_negative"))
    if rise_ms > timebase_ms:
        raise ValueError(tr(lang, "err_rise_timebase"))
    if fall_ms > timebase_ms:
        raise ValueError(tr(lang, "err_fall_timebase"))
    if edgepos not in VALID_EDGEPOS:
        raise ValueError(f"{tr(lang, 'err_edgepos')}: {', '.join(VALID_EDGEPOS)}")

    signal_duration_ms = len(bitsignal) * timebase_ms
    if interval_ms < signal_duration_ms:
        raise ValueError(f"{tr(lang, 'err_interval_short')} {format_number(signal_duration_ms)} ms.")

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
            ramp_time = rise_ms if current_level > previous_level else fall_ms
            start_time, end_time = edge_times(clock_time, ramp_time, edgepos)
            check_non_negative_edge_start(start_time, edgepos, lang)
            pairs.append((start_time, previous_level))
            pairs.append((end_time, current_level))
        previous_bit = current_bit
        previous_level = current_level

    pairs.append((interval_ms, level(bitsignal[-1])))
    return pairs


def generate_clock_signal_pairs(
    low_time_ms: float,
    high_time_ms: float,
    clocks: int,
    rise_ms: float,
    fall_ms: float,
    edgepos: str,
    high_v: float,
    low_v: float,
    lang: str = "en",
):
    if low_time_ms <= 0:
        raise ValueError(tr(lang, "err_low_time"))
    if high_time_ms <= 0:
        raise ValueError(tr(lang, "err_high_time"))
    if clocks <= 0:
        raise ValueError(tr(lang, "err_clocks"))
    if rise_ms < 0 or fall_ms < 0:
        raise ValueError(tr(lang, "err_risefall_negative"))
    if rise_ms > low_time_ms:
        raise ValueError(tr(lang, "err_rise_low"))
    if fall_ms > high_time_ms:
        raise ValueError(tr(lang, "err_fall_high"))
    if edgepos not in VALID_EDGEPOS:
        raise ValueError(f"{tr(lang, 'err_edgepos')}: {', '.join(VALID_EDGEPOS)}")

    pairs: list[tuple[float, float]] = [(0.0, low_v)]
    clock_time = 0.0

    for _ in range(clocks):
        clock_time += low_time_ms
        start_time, end_time = edge_times(clock_time, rise_ms, edgepos)
        check_non_negative_edge_start(start_time, edgepos, lang)
        pairs.append((start_time, low_v))
        pairs.append((end_time, high_v))

        clock_time += high_time_ms
        start_time, end_time = edge_times(clock_time, fall_ms, edgepos)
        check_non_negative_edge_start(start_time, edgepos, lang)
        pairs.append((start_time, high_v))
        pairs.append((end_time, low_v))

    return pairs


def build_header(config: dict[str, Any], mode: str) -> list[str]:
    lines = [
        f"{PROGRAM_NAME} Version {VERSION}",
        f"command = {config.get('command', PROGRAM_NAME)}",
        f"language = {config['language']}",
        f"timebase: {format_number(config['timebase_ms'])} [ms]",
        f"edgepos = {config['edgepos']}",
    ]
    if mode == "bitsignal":
        lines.append(f"interval = {format_number(config['interval_ms'])} [ms]")
    if abs(config["rise_ms"] - config["fall_ms"]) < 1e-12:
        if config.get("ramp_raw") is not None:
            lines.append(f"ramp = {config['ramp_raw']}")
        else:
            lines.append(f"ramp = {format_number(config['rise_ms'])} [ms]")
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


def write_output(config: dict[str, Any], pairs, filename: str | None, mode: str, header: bool) -> None:
    lang = config["language"]
    lines: list[str] = []
    if header:
        lines.extend(build_header(config, mode))
    lines.extend(f"{format_number(time_ms)} {format_number(voltage_v)}" for time_ms, voltage_v in pairs)
    text = "\n".join(lines) + "\n"

    if filename is None:
        print(text, end="")
        return

    filename = make_output_filename(filename)
    if os.path.exists(filename):
        print(f"{tr(lang, 'exists')}: {filename}")
        print()
        print(tr(lang, "would_generate"))
        for line in build_header(config, mode):
            print(line)
        answer = input(tr(lang, "overwrite")).strip().lower()
        yes_answers = ("y", "yes") if lang == "en" else ("j", "ja", "y", "yes")
        if answer not in yes_answers:
            print(tr(lang, "aborted"))
            return

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{tr(lang, 'written')}: {filename}")


def create_argument_parser(lang: str) -> argparse.ArgumentParser:
    def h(key: str) -> str:
        # argparse performs %-formatting on help strings, so literal percent signs must be escaped.
        return tr(lang, key).replace("%", "%%")

    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=tr(lang, "description"))
    parser.add_argument("-version", action="version", version=f"{PROGRAM_NAME} Version {VERSION}", help=h("version_help"))
    parser.add_argument("bitsignal", nargs="?", help=h("bitsignal_help"))
    parser.add_argument("-timebase", type=parse_time_to_ms, help=h("timebase_help"))
    parser.add_argument("-interval", type=parse_time_to_ms, help=h("interval_help"))
    parser.add_argument("-clock", nargs=3, metavar=("LOW_TIME", "HIGH_TIME", "CLOCKS"), help=h("clock_help"))
    parser.add_argument("-edgepos", choices=VALID_EDGEPOS, help=h("edgepos_help"))
    parser.add_argument("-ramp", help=h("ramp_help"))
    parser.add_argument("-rise", type=parse_time_to_ms, help=h("rise_help"))
    parser.add_argument("-fall", type=parse_time_to_ms, help=h("fall_help"))
    parser.add_argument("-signal", nargs=2, metavar=("HIGH", "LOW"), type=float, help=h("signal_help"))
    parser.add_argument("-high", type=float, help=h("high_help"))
    parser.add_argument("-low", type=float, help=h("low_help"))
    parser.add_argument("-language", choices=VALID_LANGUAGES, help=h("language_help"))
    parser.add_argument("-show", action="store_true", help=h("show_help"))
    parser.add_argument("-save", action="store_true", help=h("save_help"))
    parser.add_argument("-file", help=h("file_help"))
    parser.add_argument("-noheader", action="store_true", help=h("noheader_help"))
    return parser


def format_command(argv: list[str]) -> str:
    if not argv:
        return PROGRAM_NAME
    return " ".join([PROGRAM_NAME, *(shlex.quote(arg) for arg in argv)])


def build_config(args: argparse.Namespace, defaults: dict[str, Any], lang: str) -> dict[str, Any]:
    timebase_ms = args.timebase if args.timebase is not None else float(defaults["timebase_ms"])
    interval_ms = args.interval if args.interval is not None else float(defaults["interval_ms"])
    edgepos = args.edgepos if args.edgepos is not None else defaults["edgepos"]
    language = args.language if args.language is not None else lang
    rise_ms, fall_ms, ramp_source = resolve_rise_fall(args, defaults, timebase_ms)

    high_v = float(defaults["high_v"])
    low_v = float(defaults["low_v"])
    if args.signal is not None:
        high_v = args.signal[0]
        low_v = args.signal[1]
    if args.high is not None:
        high_v = args.high
    if args.low is not None:
        low_v = args.low

    return {
        "language": language,
        "timebase_ms": timebase_ms,
        "interval_ms": interval_ms,
        "edgepos": edgepos,
        "ramp_raw": ramp_source,
        "rise_ms": rise_ms,
        "fall_ms": fall_ms,
        "high_v": high_v,
        "low_v": low_v,
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    defaults = load_defaults()
    lang = preparse_language(argv, defaults)
    parser = create_argument_parser(lang)
    args = parser.parse_args(argv)

    if args.show:
        show_defaults(defaults, lang)
        if args.bitsignal is None and args.clock is None and not args.save:
            return 0

    config = build_config(args, defaults, lang)
    config["command"] = format_command(argv)

    if args.save:
        save_defaults(config)

    try:
        if args.clock is not None:
            low_time_ms = parse_time_to_ms(args.clock[0])
            high_time_ms = parse_time_to_ms(args.clock[1])
            try:
                clock_count = int(args.clock[2])
            except ValueError:
                raise ValueError(tr(config["language"], "err_clocks_int"))

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
                lang=config["language"],
            )
            write_output(config, pairs, args.file, mode="clock", header=not args.noheader)
            return 0

        if args.bitsignal is None:
            if args.save:
                return 0
            parser.error(tr(lang, "missing_bitsignal"))

        pairs = generate_bit_signal_pairs(
            bitsignal=args.bitsignal,
            timebase_ms=config["timebase_ms"],
            interval_ms=config["interval_ms"],
            rise_ms=config["rise_ms"],
            fall_ms=config["fall_ms"],
            edgepos=config["edgepos"],
            high_v=config["high_v"],
            low_v=config["low_v"],
            lang=config["language"],
        )
        write_output(config, pairs, args.file, mode="bitsignal", header=not args.noheader)

    except Exception as exc:
        print(f"{tr(config['language'], 'error')}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
