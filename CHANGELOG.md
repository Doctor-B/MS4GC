# Changelog

## 1.06

- Added `-invert` to exchange logical high and low signal states.
- Inversion is applied before transition generation, so configured `rise` and `fall` times follow the physical edge direction.
- Clock inversion preserves the existing time structure while exchanging logical states.
- Added `-noinvert` to disable an inversion stored in `MS4GCdefault.json`.
- Added `invert` to saved defaults and traceable output headers.
- Added inversion examples and automated tests.

## 1.05

- Added `-phase` to shift the complete generated signal in time.
- Positive phase values delay the signal; negative values advance it.
- Output is clipped to the visible time window starting at `t = 0`.
- Partially visible linear ramps are interpolated at clipping boundaries.
- Added `phase_ms` to `MS4GCdefault.json`.
- Updated English and German documentation.
- Added development acknowledgement in README files.

## 1.04

- Added English as the default language.
- Added optional German language support with `-language de`.
- Added `language` to `MS4GCdefault.json`; missing language defaults to English.
- Replaced `-header` with `-noheader`.
- Header output is enabled by default.
- Header now includes the command used to generate the file.

## 1.03

- Added `-edgepos start|center|end`.
- Changed default edge position to `center`.
- Added edge-position handling for bit signals and clock signals.

## 1.02

- Improved default handling for `ramp`, `rise`, and `fall`.
- Store either `ramp` or `rise_ms`/`fall_ms`, not both.
- Read `MS4GCdefault.json` at program startup.

## 1.01

- Added program version.
- Added `-version`.
- Replaced `clock` timebase with `timebase`.
- Added `-clock LOW_TIME HIGH_TIME CLOCKS` for clock-signal generation.

## 1.00

- Initial MS4GC concept.
- Generate time/voltage pairs from binary sequences.
- Support `ramp`, `rise`, `fall`, `high`, `low`, `file`, `show`, and `save`.
