#Hier werden Parameter denfiniert, die für das Programm einfach von hier zu ändern sind. 
BEGIN_BUTTON_PIN = 17 #GPIO Pin für den Startknopf
POWER_BUTTON_PIN = 27 #GPIO Pin für den Powerknopf

ACCELEROMETER_I2C_ADDRESS = 0x1C #I2C Adresse des Beschleunigungssensors

HALL_ENABLED = True #Ob der Hall Sensor (Drehzahlsensor) verwendet wird
HALL_SENSOR_PIN = 22 #GPIO Pin für den Hall Sensor
HALL_PULL_UP = True #Ob ein Pull-Up Widerstand verwendet wird (True für Open-Collector Sensoren)
HALL_POLL_HZ = 800 #Abtastrate für den Hall Sensor im Threaded-Modus (Hz)
HALL_STABLE_SAMPLES = 5 #Anzahl aufeinanderfolgender HIGH-Samples, bevor der Hall Sensor wieder für die nächste Erfassung bereit ist

IDLE_LED_PIN = 5 #GPIO Pin für die Idle LED
MEASURING_LED_PIN = 6 #GPIO Pin für die Mess-LED
MEASURING_LED_BLINK_INTERVAL = 0.5 #Blinkintervall der Mess-LED in Sekunden
USB_COPY_LED_PIN = 13 #GPIO Pin für die USB Copy LED
USB_COPY_LED_BLINK_INTERVAL = 0.2 #Blinkintervall der USB Copy LED in Sekunden

READING_INTERVAL = 1.0 #Intervall für das Auslesen des Beschleunigungssensors während der Messung in Sekunden

CSV_OUTPUT_PATH = "measurements.csv" #Pfad für die Ausgabe der Messdaten als CSV-Datei
USB_COPY_ANY = True #Ob die Messdaten auf alle gefundenen USB-Laufwerke kopiert werden sollen
USB_CHECK_INTERVAL = 1.0 #Intervall für die Überprüfung auf neu eingesteckte USB-Laufwerke in Sekunden