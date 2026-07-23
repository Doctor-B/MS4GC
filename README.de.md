# MS4GC – MakeSignal4GoConfigure

**MS4GC** ist ein kleines Python-Kommandozeilenwerkzeug zur Erzeugung von Zeit-/Spannungs-Wertepaaren für benutzerdefinierte Signale.

Das Programm kann aus Bitfolgen wie `0011010` eine Signaldatei erzeugen oder mit `-clock` ein periodisches Low-/High-Taktsignal mit konfigurierbaren Anstiegs- und Abfallzeiten erzeugen. Zeiten werden in Millisekunden ausgegeben, Spannungen in Volt.

Die erzeugten `.dat`-Dateien können entweder mit einem nachvollziehbaren Parameter-Header oder mit `-noheader` als reine Wertepaare geschrieben werden. Die reine Wertepaarausgabe ist für den direkten Import in Signaldefinitions-Werkzeuge gedacht. Der primäre Anwendungsfall ist Renesas Go Configure™ Software Hub, zum Beispiel zur Konfiguration einer Spannungsquelle über einen Custom-Signal-Import wie „Custom Signal“ / „Import Points“, abhängig von der installierten Go-Configure-Version und der ausgewählten Bauteilfamilie.

MS4GC unterstützt konfigurierbare High- und Low-Pegel, negative Spannungen, individuelle Rise- und Fall-Zeiten, absichtlich pro Aufruf aktivierte logische Signalinvertierung, Defaultwerte in `MS4GCdefault.json`, Flankenpositionen, Sprachauswahl und Phasenverschiebung.

Die englische Hauptdokumentation steht in [`README.md`](README.md).

## Funktionen

- Erzeugung von Wertepaaren aus Bitfolgen, z. B. `0011010`
- Erzeugung von Taktsignalen mit `-clock LOW_TIME HIGH_TIME CLOCKS`
- Konfiguration von `timebase`, `interval`, `ramp`, `rise`, `fall`, `high` und `low`
- Zeitliche Verschiebung des Signals mit `-phase`
- absichtliche Invertierung der logischen High-/Low-Zustände für einen einzelnen Aufruf mit `-invert`
- Wahl der Flankenposition mit `-edgepos start|center|end`
- Speicherung von Defaultwerten in `MS4GCdefault.json`
- Englisch als Standardsprache, Deutsch mit `-language de`
- Ausgabe mit Header oder reine Import-Wertepaare mit `-noheader`

## Voraussetzungen

- Python 3.10 oder neuer wird empfohlen
- Es werden keine externen Python-Pakete benötigt

## Schnellstart

```bash
python MS4GC.py -noheader 0011010
```

Beispielausgabe:

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

Die Defaultwerte sind:

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

## Ausgabe mit und ohne Header

Standardmäßig schreibt MS4GC einen Parameter-Header. Der Header enthält die verwendete Kommandozeile, damit die Datei später nachvollziehbar bleibt.

```bash
python MS4GC.py -file Signal 0011010
```

Beispiel-Header:

```text
MS4GC Version 1.06a
command = MS4GC -file Signal 0011010
language = en
timebase = 1.0 [ms]
phase = 0.0 [ms]
invert = false
edgepos = center
interval = 20.0 [ms]
ramp = 1%
high = 5.0 [V]
low = 0.0 [V]
```

Für Import-Workflows, die reine Wertepaare benötigen, verwende `-noheader`:

```bash
python MS4GC.py -noheader -file Signal 0011010
```

Fehlt die Endung `.dat`, wird sie automatisch ergänzt.

## Bitfolgenmodus

Das Positionsargument ist eine Bitfolge:

```bash
python MS4GC.py 0011010
```

Jedes Bit belegt eine `timebase`. Ein Wechsel von `0` nach `1` erzeugt eine steigende Flanke, ein Wechsel von `1` nach `0` eine fallende Flanke.

```bash
python MS4GC.py -timebase 2ms -ramp 0.05ms -high 3.3 -low 0 0011010
```

## Taktsignalmodus

Der Taktsignalmodus nutzt drei Argumente:

```bash
python MS4GC.py -clock LOW_TIME HIGH_TIME CLOCKS
```

Beispiel:

```bash
python MS4GC.py -noheader -clock 0.48 0.51 2
```

Mit dem Default `edgepos=center` beginnt die Ausgabe so:

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

Im Taktsignalmodus wird `interval` nicht verwendet. Das sichtbare Ausgabefenster ergibt sich aus dem erzeugten Taktsignal selbst.

## Flankenposition

`-edgepos` legt fest, wie der ideale Umschaltzeitpunkt zur linearen Flanke liegt:

```text
start   die Flanke beginnt beim Umschaltzeitpunkt
center  die Flankenmitte liegt beim Umschaltzeitpunkt
end     die Flanke ist beim Umschaltzeitpunkt abgeschlossen
```

Default:

```text
-edgepos center
```

Für eine steigende Flanke mit `rise = 0.01ms` beim Umschaltzeitpunkt `t = 2.0ms`:

```text
start:   2.000ms -> 2.010ms
center:  1.995ms -> 2.005ms
end:     1.990ms -> 2.000ms
```

## Phase

`-phase` verschiebt das gesamte erzeugte Signal zeitlich.

```text
positive phase  -> Signal kommt später
negative phase  -> Signal kommt früher
```

Beispiel:

```bash
python MS4GC.py -noheader -timebase 1ms -phase -2ms 0010100
```

Die Ausgabe beginnt immer bei `t = 0`. Punkte außerhalb des sichtbaren Zeitfensters werden abgeschnitten. Ist eine lineare Flanke am Anfang oder Ende des Fensters nur teilweise sichtbar, interpoliert MS4GC die Spannung an der Schnittgrenze.

Das bedeutet: Mit `edgepos=center` kann eine genau bei `t = 0` zentrierte Flanke einen interpolierten Startwert wie `2.5V` bei einem Übergang von `0V` nach `5V` erzeugen.

## Signalinvertierung

`-invert` vertauscht die logischen High- und Low-Zustände, bevor die Flanken erzeugt werden. Zeitlicher Verlauf, Phase und Umschaltzeitpunkte bleiben unverändert.

```bash
python MS4GC.py -noheader -invert 0010100
```

Die Bitfolge wird damit wie ihr logisches Gegenstück behandelt:

```text
0010100 -> 1101011
```

Die Invertierung erfolgt vor der Anwendung von `rise` und `fall`. Wird eine Flanke durch die Invertierung physikalisch fallend, verwendet sie daher die konfigurierte Fall-Zeit. Eine physikalisch steigende Flanke verwendet die Rise-Zeit.

Im Clock-Modus bleibt die Zeitstruktur erhalten: Das Signal beginnt High, wechselt nach `LOW_TIME` zu Low und nach `HIGH_TIME` wieder zu High. Eine andere Interpretation der Clock-Zeitabschnitte kann später über eine getrennte Option ergänzt werden.

`-invert` wird absichtlich nicht in `MS4GCdefault.json` gespeichert. Die Option muss bei jedem Aufruf ausdrücklich angegeben werden, wenn das Signal invertiert werden soll. Dadurch werden überraschende Ausgaben durch eine früher gespeicherte Invertierung vermieden.

## Rise, Fall und Ramp

`-ramp` setzt Rise und Fall gemeinsam:

```bash
python MS4GC.py -ramp 1% 0011010
python MS4GC.py -ramp 0.01ms 0011010
```

`-rise` und `-fall` können unabhängig gesetzt werden:

```bash
python MS4GC.py -rise 10us -fall 50us 0011010
```

Sind Rise und Fall gleich, wird nur `ramp` in `MS4GCdefault.json` gespeichert. Sind Rise und Fall verschieden, werden nur `rise_ms` und `fall_ms` gespeichert.

## Spannungspegel

Defaultwerte sind `5V` für High und `0V` für Low.

```bash
python MS4GC.py -high 3.3 -low 0 0011010
python MS4GC.py -signal 2.5 -2.5 0011010
```

## Defaultwerte

MS4GC liest `MS4GCdefault.json` bei jedem Start aus dem aktuellen Arbeitsverzeichnis.

Defaultwerte anzeigen:

```bash
python MS4GC.py -show
```

Aktuelle Werte speichern:

```bash
python MS4GC.py -language de -timebase 2ms -phase -0.5ms -edgepos center -ramp 2% -save
```

Beispiel:

```json
{
    "version": "1.06a",
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

Fehlt `language`, wird Englisch verwendet. Ein alter `invert`-Eintrag in `MS4GCdefault.json` wird ignoriert; Invertierung ist nur aktiv, wenn `-invert` in der Kommandozeile angegeben wird.

## Hilfe und Version

```bash
python MS4GC.py -help
python MS4GC.py -version
python MS4GC.py -language de -help
```

## Tests

Tests aus dem Hauptverzeichnis ausführen:

```bash
python -m unittest discover -s tests
```

## Hinweis zur Erstellung

Dieses Projekt wurde von Peter Beck mit Unterstützung von OpenAI ChatGPT entwickelt. Der erzeugte Code, die Dokumentation und die Beispiele wurden vor der Veröffentlichung vom Repository-Inhaber geprüft und angepasst.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [`LICENSE`](LICENSE).
