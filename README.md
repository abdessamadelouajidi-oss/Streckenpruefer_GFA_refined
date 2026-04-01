# Streckenpruefer GFA refined

Dieses Projekt ist ein Raspberry-Pi-basiertes Messsystem zur Erfassung von Vibrationsdaten. Es liest einen Beschleunigungssensor per I2C aus, zaehlt optional Impulse eines Hall-Sensors, zeigt den Systemzustand ueber LEDs an und speichert Messdaten als CSV-Datei. Beim Einstecken eines USB-Datentraegers kann die CSV-Datei automatisch auf das erkannte Laufwerk kopiert werden.

## Funktionsueberblick

- Start und Stop der Messung ueber einen BEGIN-Taster
- Sicheres Beenden ueber einen POWER-Taster mit Haltefunktion
- Auslesen von Beschleunigungswerten `ax`, `ay` und `az`
- Optionales Mitzaehlen von Dreh- oder Triggerimpulsen ueber einen Hall-Sensor
- Statusanzeige ueber drei LEDs:
  - `IdleLED`: System bereit
  - `MeasuringLED`: Messung aktiv, blinkt waehrend der Aufnahme
  - `CopyLED`: USB-Kopiervorgang aktiv oder abgeschlossen
- Speicherung der Messwerte in `measurements.csv`
- Automatisches Kopieren der CSV-Datei auf neu erkannte USB-Mounts

## Projektaufbau

- `main.py`: Einstiegspunkt und zentrale Ablaufsteuerung
- `config.py`: Alle anpassbaren GPIO-, Timing- und Dateiparameter
- `VibrationSensor.py`: Ansteuerung des Beschleunigungssensors per I2C
- `HallSensor.py`: Hintergrund-Thread zur Impulszaehlung des Hall-Sensors
- `LEDs.py`: LED-Klassen fuer Bereitschaft, Messung und USB-Kopierstatus
- `buttons.py`: Tasterlogik fuer Start und Shutdown
- `StateMachine.py`: Einfache Zustandsmaschine mit `IDLE` und `MEASURING`
- `DistanceSensor.py`: Derzeit leer und nicht in den Hauptablauf eingebunden

## Hardware-Annahmen

Das Projekt ist fuer einen Raspberry Pi mit GPIO-Unterstuetzung ausgelegt.

- Beschleunigungssensor an I2C-Adresse `0x1D`
- Hall-Sensor optional an GPIO `22`
- BEGIN-Taster an GPIO `17`
- POWER-Taster an GPIO `27`
- Idle-LED an GPIO `5`
- Measuring-LED an GPIO `6`
- USB-Copy-LED an GPIO `13`

Die Standardbelegung kann in `config.py` angepasst werden.

## Software-Voraussetzungen

- Python `3.10.6` wurde laut Quelltext verwendet und getestet
- Raspberry-Pi-Umgebung mit GPIO-Zugriff
- I2C auf dem Raspberry Pi aktiviert
- Abhaengigkeiten aus `requirements.txt`

Installation der Python-Pakete:

```bash
pip install -r requirements.txt
```

Je nach Betriebssystem-Image kann es zusaetzlich notwendig sein, systemseitige GPIO- oder SMBus-Pakete zu installieren.

## Konfiguration

Die wichtigsten Parameter werden in `config.py` gepflegt:

- GPIO-Pins fuer Taster, LEDs und Hall-Sensor
- I2C-Adresse des Beschleunigungssensors
- Aktivierung des Hall-Sensors ueber `HALL_ENABLED`
- Abtastintervall der Messung ueber `READING_INTERVAL`
- Zielpfad der CSV-Datei ueber `CSV_OUTPUT_PATH`
- Automatische USB-Kopie ueber `USB_COPY_ANY`
- Intervall fuer USB-Erkennung ueber `USB_CHECK_INTERVAL`

## Ablauf der Messung

1. Beim Start initialisiert das System die Zustandsmaschine, den Beschleunigungssensor, optional den Hall-Sensor, die Taster und die LEDs.
2. Die `IdleLED` signalisiert den Bereitschaftszustand.
3. Ein Druck auf den BEGIN-Taster startet die Messung.
4. Waehrend der Messung werden in festem Intervall Beschleunigungswerte und der aktuelle Hall-Zaehlerstand erfasst.
5. Ein weiterer Druck auf BEGIN beendet die Messung und schaltet zurueck in den Bereitschaftszustand.
6. Der POWER-Taster fuehrt bei langem Halten einen geregelten Stop aus und speichert die Messdaten.
7. Wird ein neuer USB-Datentraeger erkannt, wird die CSV-Datei automatisch dorthin kopiert.

## CSV-Ausgabe

Die erzeugte CSV-Datei enthaelt aktuell folgende Spalten:

- `timestamp`
- `ax`
- `ay`
- `az`
- `spin_count`

Die Datei wird standardmaessig als `measurements.csv` im Projektverzeichnis geschrieben.

## Programmstart

Das System wird ueber `main.py` gestartet:

```bash
python main.py
```

## Hinweise

- Das Projekt ist fuer echte Hardware ausgelegt. Ohne Raspberry Pi, GPIO und I2C-Sensorik ist nur ein eingeschraenkter Test moeglich.
- In `buttons.py` ist fuer fehlendes `RPi.GPIO` ein begrenzter Simulationsmodus vorgesehen. Die restlichen Module setzen jedoch reale Hardware voraus.
- USB-Kopie funktioniert nur, wenn das Zielmedium unter `/media/` oder `/mnt/` gemountet ist und als passendes Dateisystem erkannt wird.
