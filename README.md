# MS4GC – MakeSignal4GoConfigure

**MS4GC** is a small command-line tool that generates plain time/voltage point pairs for custom signal definitions.

It can create signals from binary sequences such as `0011010` or generate periodic low/high clock signals with configurable rise and fall times. Time values are written in milliseconds, voltage values in volts.

The generated `.dat` files include a parameter header by default so the generation settings and command-line arguments remain traceable. Use `-noheader` to create point-pair-only files for import workflows in signal-generator or device-configuration software. The primary target use case is **Renesas Go Configure™ Software Hub**, for example when configuring a voltage source using a custom signal import workflow such as **Custom Signal** / **Import Points** in the **Custom Signal Wizard**. Exact UI labels may vary depending on the installed Go Configure version and selected device family.

MS4GC supports configurable high and low voltage levels, negative voltages, custom rise and fall times, default settings stored in `MS4GCdefault.json`, and edge-positioning modes where the ideal switching time can refer to the start, center, or end of a transition.

German documentation is available in [`README.de.md`](README.de.md).

## Features

- Generate time/voltage point pairs from a binary sequence.
- Generate periodic low/high clock signals with `-clock`.
- Use configurable `high` and `low` voltage levels, including negative values.
- Configure a common ramp time or separate rise and fall times.
- Choose the edge position with `-edgepos start|center|end`.
- Store defaults in `MS4GCdefault.json`.
- Use English by default and German via `-language de` or the default file.
- Write directly to `.dat` files.
- Suppress the default parameter header with `-noheader` for direct import files.
- Include the used command-line arguments in the default header for traceability.

## Requirements

- Python 3.10 or newer is recommended.
- No external Python packages are required.

## Quick start

```bash
python MS4GC.py 0011010
```

Output:

```text
MS4GC Version 1.04
command = MS4GC 0011010
language = en
timebase: 1.0 [ms]
edgepos = center
interval = 20.0 [ms]
ramp = 1%
high = 5.0 [V]
low = 0.0 [V]
0.0 0.0
1.995 0.0
2.005 5.0
3.995 5.0
4.005 0.0
4.995 0.0
5.005 5.0
5.995 5.0
6.005 0.0
20.0 0.0
```

By default, MS4GC uses:

```text
language = en
timebase = 1 ms
interval = 20 ms
ramp = 1% of timebase = 0.01 ms
edgepos = center
high = 5 V
low = 0 V
```

## Save output to a file

```bash
python MS4GC.py -file Signal 0011010
```

This writes `Signal.dat`. If the file already exists, MS4GC shows the generation parameters and asks before overwriting it.

The extension `.dat` is added automatically if missing.

## Header and import mode

By default, MS4GC writes a parameter header before the generated point pairs. The header also includes the command-line arguments used for generation, which makes the file easier to reproduce later.

Use `-noheader` when a target tool expects plain point lists only:

```bash
python MS4GC.py -noheader -file Signal 0011010
```

Example default header:

```text
MS4GC Version 1.04
command = MS4GC -file Signal 0011010
language = en
timebase: 1.0 [ms]
edgepos = center
interval = 20.0 [ms]
ramp = 1%
high = 5.0 [V]
low = 0.0 [V]
```

## Clock signal mode

Use `-clock LOW_TIME HIGH_TIME CLOCKS` to generate a clock signal.

```bash
python MS4GC.py -clock 0.48 0.51 2
```

With the default ramp of `0.01 ms` and `edgepos=center`, this produces:

```text
0.0 0.0
0.475 0.0
0.485 5.0
0.985 5.0
0.995 0.0
1.465 0.0
1.475 5.0
1.975 5.0
1.985 0.0
```

`LOW_TIME` and `HIGH_TIME` are interpreted as milliseconds if no unit is given. `CLOCKS` is the number of low/high cycles.

## Edge positioning

`-edgepos` controls how the ideal switching time is interpreted relative to the ramp.

| Value | Meaning |
|---|---|
| `start` | The edge starts at the ideal switching time. |
| `center` | The center of the edge is at the ideal switching time. This is the default. |
| `end` | The edge is complete at the ideal switching time. |

Example with a rising edge at `t = 0.48 ms` and `ramp = 0.01 ms`:

| Mode | Generated edge points |
|---|---|
| `start` | `0.48 0.0` → `0.49 5.0` |
| `center` | `0.475 0.0` → `0.485 5.0` |
| `end` | `0.47 0.0` → `0.48 5.0` |

## Time values

All output times are in milliseconds. Input times may use units:

```text
ns, us, µs, ms, s
```

Examples:

```bash
python MS4GC.py -timebase 2ms 0011010
python MS4GC.py -rise 10us -fall 20us 0011010
python MS4GC.py -clock 480us 510us 20
```

If no unit is given, milliseconds are assumed.

## Voltage levels

Default levels are:

```text
high = 5 V
low = 0 V
```

Set both levels:

```bash
python MS4GC.py -signal 3.3 0 0011010
```

Set only one level:

```bash
python MS4GC.py -high 2.5 0011010
python MS4GC.py -low -1.0 0011010
```

Negative voltages are allowed.

## Defaults file

On every run, MS4GC first checks whether `MS4GCdefault.json` exists in the current working directory. If it exists, it is loaded and used.

Save current settings:

```bash
python MS4GC.py -language de -edgepos center -ramp 1% -high 5 -low 0 -save
```

Example `MS4GCdefault.json`:

```json
{
    "version": "1.04",
    "language": "de",
    "timebase_ms": 1.0,
    "interval_ms": 20.0,
    "edgepos": "center",
    "high_v": 5.0,
    "low_v": 0.0,
    "ramp": "1%"
}
```

If `language` is missing, English is used. Currently supported values are:

```text
en
de
```

If rise and fall are equal, only `ramp` is stored. If they differ, only `rise_ms` and `fall_ms` are stored.

## Show defaults

```bash
python MS4GC.py -show
```

## German output and help

Temporarily use German:

```bash
python MS4GC.py -language de -show
python MS4GC.py -language de -help
```

Save German as the default language:

```bash
python MS4GC.py -language de -save
```

## Command-line reference

```text
MS4GC [-h] [-version] [-timebase TIMEBASE] [-interval INTERVAL]
      [-clock LOW_TIME HIGH_TIME CLOCKS]
      [-edgepos {start,center,end}] [-ramp RAMP]
      [-rise RISE] [-fall FALL] [-signal HIGH LOW]
      [-high HIGH] [-low LOW] [-language {en,de}]
      [-show] [-save] [-file FILE] [-noheader]
      [bitsignal]
```

## Examples

Generate a bit-sequence signal:

```bash
python MS4GC.py 0011010
```

Generate a clock signal:

```bash
python MS4GC.py -clock 0.48 0.51 20
```

Generate a clock signal with the old start-edge behavior:

```bash
python MS4GC.py -edgepos start -clock 0.48 0.51 20
```

Generate a bipolar signal:

```bash
python MS4GC.py -signal 2.5 -2.5 0011010
```

Write a `.dat` file with point pairs only for import:

```bash
python MS4GC.py -noheader -file import_signal 0011010
```

## Testing

Run the tests with:

```bash
python -m unittest discover -s tests
```

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
