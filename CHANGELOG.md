# Changelog

## 1.04

- Added language support with English as the default language.
- Added `-language {en,de}`.
- Added `language` to `MS4GCdefault.json`.
- If `language` is missing in the default file, English is used.
- Added German help and output messages.
- Changed output behavior before release: the parameter header is now enabled by default again for traceability.
- Replaced `-header` with `-noheader` for direct import workflows that require point pairs only.
- Added the used command-line arguments to the default header.
- Updated README documentation and added `README.de.md`.

## 1.03

- Added `-edgepos {start,center,end}`.
- Set `edgepos=center` as the default.
- Added edge-position handling for bit-sequence and clock-signal generation.

## 1.02

- `MS4GCdefault.json` is loaded at the beginning of every run.
- Defaults store either `ramp` or separate `rise_ms` and `fall_ms`, never both.
- `-show` displays either `ramp` or `rise`/`fall`, depending on the stored mode.

## 1.01

- Added program version handling with `-version`.
- Renamed the old `-clock` time base option to `-timebase`.
- Added `-clock LOW_TIME HIGH_TIME CLOCKS` for periodic clock-signal generation.

## 1.00

- Initial version.
- Generate time/voltage point pairs from a bit sequence.
- Add configurable timebase, interval, ramp, rise/fall, high/low voltage levels, file output, and defaults.
