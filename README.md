# MS4GC – MakeSignal4GoConfigure

**MS4GC** is a small Python command-line tool that generates time/voltage point pairs for custom signal definitions.

It can create signals from binary sequences such as `0011010` or generate periodic low/high clock signals with configurable rise and fall times. Time values are written in milliseconds, voltage values in volts.

The generated `.dat` files can be written either with a traceable parameter header or as plain point pairs using `-noheader`. Plain point-pair output is intended for direct import into signal-definition tools. The primary target use case is Renesas Go Configure™ Software Hub, for example when configuring a voltage source with a custom-signal import workflow such as “Custom Signal” / “Import Points”, depending on the installed Go Configure version and the selected device family.

MS4GC supports configurable high and low voltage levels, negative voltages, custom rise and fall times, default settings stored in `MS4GCdefault.json`, edge positioning modes, language selection, and phase shifting.

German documentation is available in [`README.de.md`](README.de.md).

## Features

- Generate point pairs from binary sequences, for example `0011010`
- Generate clock signals with `-clock LOW_TIME HIGH_TIME CLOCKS`
- Configure `timebase`, `interval`, `ramp`, `rise`, `fall`, `high`, and `low`
- Shift the generated signal with `-phase`
- Select edge alignment with `-edgepos start|center|end`
- Store defaults in `MS4GCdefault.json`
- English default language, optional German output with `-language de`
- Write traceable output with a header or import-ready point pairs with `-noheader`

## Requirements

- Python 3.10 or newer is recommended
- No external Python packages are required

## Quick start

```bash
python MS4GC.py -noheader 0011010
```

Example output:

```text
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

The default values are:

```text
language = en
timebase = 1.0 ms
interval = 20.0 ms
phase = 0.0 ms
edgepos = center
ramp = 1%
high = 5.0 V
low = 0.0 V
```

## Output with and without header

By default, MS4GC writes a parameter header. The header includes the command that was used to generate the data, so the output is traceable later.

```bash
python MS4GC.py -file Signal 0011010
```

Example header:

```text
MS4GC Version 1.05
command = MS4GC -file Signal 0011010
language = en
timebase = 1.0 [ms]
phase = 0.0 [ms]
edgepos = center
interval = 20.0 [ms]
ramp = 1%
high = 5.0 [V]
low = 0.0 [V]
```

For import workflows that require plain point pairs, use `-noheader`:

```bash
python MS4GC.py -noheader -file Signal 0011010
```

If `.dat` is missing from the filename, MS4GC appends it automatically.

## Bit-signal mode

The positional argument is a binary sequence:

```bash
python MS4GC.py 0011010
```

Each bit occupies one `timebase` period. A transition from `0` to `1` creates a rising edge; a transition from `1` to `0` creates a falling edge.

```bash
python MS4GC.py -timebase 2ms -ramp 0.05ms -high 3.3 -low 0 0011010
```

## Clock mode

Clock mode uses three arguments:

```bash
python MS4GC.py -clock LOW_TIME HIGH_TIME CLOCKS
```

Example:

```bash
python MS4GC.py -noheader -clock 0.48 0.51 2
```

With the default `edgepos=center`, output begins like this:

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

In clock mode, `interval` is not used. The visible output window is determined by the generated clock signal itself.

## Edge positioning

`-edgepos` controls how the ideal switching time relates to the linear transition:

```text
start   transition starts at the switching time
center  transition center is at the switching time
end     transition is completed at the switching time
```

Default:

```text
-edgepos center
```

For a rising edge with `rise = 0.01ms` at switching time `t = 2.0ms`:

```text
start:   2.000ms -> 2.010ms
center:  1.995ms -> 2.005ms
end:     1.990ms -> 2.000ms
```

## Phase shifting

`-phase` shifts the entire generated signal in time.

```text
positive phase  -> signal is delayed
negative phase  -> signal is advanced
```

Example:

```bash
python MS4GC.py -noheader -timebase 1ms -phase -2ms 0010100
```

The output always starts at `t = 0`. Points outside the visible time window are clipped. If a linear transition is partially visible at the beginning or end of the window, MS4GC interpolates the voltage at the clipping boundary.

This means that with `edgepos=center`, a transition centered exactly at `t = 0` can produce an interpolated start value such as `2.5V` for a `0V` to `5V` transition.

## Rise, fall, and ramp

`-ramp` sets both rise and fall time:

```bash
python MS4GC.py -ramp 1% 0011010
python MS4GC.py -ramp 0.01ms 0011010
```

`-rise` and `-fall` can be used independently:

```bash
python MS4GC.py -rise 10us -fall 50us 0011010
```

If rise and fall are equal, only `ramp` is stored in `MS4GCdefault.json`. If rise and fall differ, only `rise_ms` and `fall_ms` are stored.

## Voltage levels

Default levels are `5V` for high and `0V` for low.

```bash
python MS4GC.py -high 3.3 -low 0 0011010
python MS4GC.py -signal 2.5 -2.5 0011010
```

## Defaults

MS4GC reads `MS4GCdefault.json` from the current working directory at every start.

Show defaults:

```bash
python MS4GC.py -show
```

Save current values as defaults:

```bash
python MS4GC.py -language de -timebase 2ms -phase -0.5ms -edgepos center -ramp 2% -save
```

Example default file:

```json
{
    "version": "1.05",
    "language": "de",
    "timebase_ms": 2.0,
    "interval_ms": 20.0,
    "phase_ms": -0.5,
    "edgepos": "center",
    "high_v": 5.0,
    "low_v": 0.0,
    "ramp": "2%"
}
```

If `language` is missing, English is used.

## Help and version

```bash
python MS4GC.py -help
python MS4GC.py -version
python MS4GC.py -language de -help
```

## Tests

Run the test suite from the repository root:

```bash
python -m unittest discover -s tests
```

## Development note

This project was developed by Andreas Beck with assistance from OpenAI ChatGPT. The generated code, documentation, and examples were reviewed and adapted by the repository owner before publication.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
