# MS4GC – MakeSignal4GoConfigure

**MS4GC** ist ein kleines Kommandozeilenprogramm zum Erzeugen von Zeit-/Spannungs-Wertepaaren für benutzerdefinierte Signaldefinitionen.

Das Programm kann aus einer Bitfolge wie `0011010` eine Signaldatei erzeugen oder mit `-clock` ein periodisches Low-/High-Taktsignal erzeugen. Die Zeiten werden in Millisekunden ausgegeben, die Spannungen in Volt.

Die erzeugten `.dat`-Dateien enthalten standardmäßig einen Parameter-Header, damit die Erzeugungsparameter und Kommandozeilenargumente nachvollziehbar bleiben. Mit `-noheader` werden reine Wertepaare für Import-Workflows in Signalgenerator- oder Bauteilkonfigurationssoftware erzeugt. Der primäre Anwendungsfall ist **Renesas Go Configure™ Software Hub**, zum Beispiel zur Konfiguration einer Spannungsquelle über einen Custom-Signal-Import wie **Custom Signal** / **Import Points** im **Custom Signal Wizard**. Die exakten Bezeichnungen in der Oberfläche können je nach Go-Configure-Version und ausgewählter Bauteilfamilie abweichen.

MS4GC unterstützt konfigurierbare High- und Low-Pegel, negative Spannungen, eigene Rise- und Fall-Zeiten, Defaultwerte in `MS4GCdefault.json` und Flankenpositionen, bei denen der ideale Umschaltzeitpunkt am Anfang, in der Mitte oder am Ende der Flanke liegen kann.

Die englische Hauptdokumentation steht in [`README.md`](README.md).

## Funktionen

- Erzeugung von Zeit-/Spannungs-Wertepaaren aus einer Bitfolge.
- Erzeugung periodischer Low-/High-Taktsignale mit `-clock`.
- Konfigurierbare `high`- und `low`-Spannungspegel, auch negativ.
- Gemeinsame Rampenzeit oder getrennte Rise-/Fall-Zeiten.
- Flankenposition mit `-edgepos start|center|end`.
- Speichern von Defaults in `MS4GCdefault.json`.
- Englisch als Standardsprache, Deutsch über `-language de` oder die Defaultdatei.
- Direkte Ausgabe in `.dat`-Dateien.
- Unterdrücken des standardmäßigen Parameter-Headers mit `-noheader` für direkte Importdateien.
- Aufnahme der verwendeten Kommandozeilenargumente in den Standard-Header zur Nachvollziehbarkeit.

## Voraussetzungen

- Empfohlen: Python 3.10 oder neuer.
- Es werden keine externen Python-Pakete benötigt.

## Schnellstart

```bash
python MS4GC.py 0011010
```

Ausgabe:

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

Standardwerte:

```text
language = en
timebase = 1 ms
interval = 20 ms
ramp = 1% von timebase = 0.01 ms
edgepos = center
high = 5 V
low = 0 V
```

## Ausgabe in Datei speichern

```bash
python MS4GC.py -file Signal 0011010
```

Das schreibt `Signal.dat`. Wenn die Datei bereits existiert, zeigt MS4GC die Erzeugungsparameter an und fragt vor dem Überschreiben nach.

Die Endung `.dat` wird automatisch ergänzt, falls sie fehlt.

## Header und Importmodus

Standardmäßig schreibt MS4GC einen Parameter-Header vor die erzeugten Wertepaare. Der Header enthält auch die verwendeten Kommandozeilenargumente, damit die Datei später leichter reproduziert werden kann.

Mit `-noheader` wird eine reine Punktliste erzeugt, falls ein Zielwerkzeug nur Wertepaare erwartet:

```bash
python MS4GC.py -noheader -file Signal 0011010
```

Beispiel für den Standard-Header:

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

## Taktsignal mit `-clock`

```bash
python MS4GC.py -clock 0.48 0.51 2
```

Mit `ramp = 0.01 ms` und `edgepos=center` entsteht:

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

`LOW_TIME` und `HIGH_TIME` werden als Millisekunden interpretiert, wenn keine Einheit angegeben ist. `CLOCKS` ist die Anzahl der Low-/High-Zyklen.

## Flankenposition

`-edgepos` legt fest, wie der ideale Umschaltzeitpunkt relativ zur Rampe interpretiert wird.

| Wert | Bedeutung |
|---|---|
| `start` | Die Flanke beginnt beim idealen Umschaltzeitpunkt. |
| `center` | Die Flankenmitte liegt beim idealen Umschaltzeitpunkt. Das ist der Default. |
| `end` | Die Flanke ist beim idealen Umschaltzeitpunkt abgeschlossen. |

Beispiel für eine steigende Flanke bei `t = 0.48 ms` und `ramp = 0.01 ms`:

| Modus | Erzeugte Flankenpunkte |
|---|---|
| `start` | `0.48 0.0` → `0.49 5.0` |
| `center` | `0.475 0.0` → `0.485 5.0` |
| `end` | `0.47 0.0` → `0.48 5.0` |

## Zeitangaben

Alle Ausgabezeiten sind in Millisekunden. Eingaben können Einheiten verwenden:

```text
ns, us, µs, ms, s
```

Beispiele:

```bash
python MS4GC.py -timebase 2ms 0011010
python MS4GC.py -rise 10us -fall 20us 0011010
python MS4GC.py -clock 480us 510us 20
```

Ohne Einheit wird Millisekunden angenommen.

## Spannungspegel

Defaultwerte:

```text
high = 5 V
low = 0 V
```

Beide Pegel setzen:

```bash
python MS4GC.py -signal 3.3 0 0011010
```

Nur einen Pegel setzen:

```bash
python MS4GC.py -high 2.5 0011010
python MS4GC.py -low -1.0 0011010
```

Negative Spannungen sind erlaubt.

## Defaultdatei

Bei jedem Aufruf prüft MS4GC zuerst, ob `MS4GCdefault.json` im aktuellen Arbeitsverzeichnis existiert. Falls ja, wird sie geladen und verwendet.

Aktuelle Einstellungen speichern:

```bash
python MS4GC.py -language de -edgepos center -ramp 1% -high 5 -low 0 -save
```

Beispiel:

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

Wenn `language` fehlt, wird Englisch verwendet. Aktuell unterstützt:

```text
en
de
```

Wenn Rise und Fall gleich sind, wird nur `ramp` gespeichert. Wenn sie verschieden sind, werden nur `rise_ms` und `fall_ms` gespeichert.

## Defaults anzeigen

```bash
python MS4GC.py -show
```

## Deutsche Ausgabe und Hilfe

Deutsch temporär verwenden:

```bash
python MS4GC.py -language de -show
python MS4GC.py -language de -help
```

Deutsch als Standardsprache speichern:

```bash
python MS4GC.py -language de -save
```

## Tests

```bash
python -m unittest discover -s tests
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [`LICENSE`](LICENSE).
