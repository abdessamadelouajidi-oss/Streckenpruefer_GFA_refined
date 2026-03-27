#Das Projekt wird mit Python 3.10.6 erstellt und getestet. Es könnte sein, dass es mit anderen Versionen nicht funktioniert.
#Das Projekt wird später für die Bewrtung auf GitHub verföffentlicht.

import csv #Modul zum Lesen und Schreiben von CSV Dateien
import time #Zeitbezogene Funktionen für Timestampausgabe
import os
import shutil # Utility Funktionen für das Kopieren und Kreeieren von csv Dateien
from StateMachine import StateMachine  #Import der StateMachine Klasse
from HallSensor import HallSensor
from LEDs import MeasuringLED, IdleLED, CopyLED #Import der LED Klassen
from buttons import BeginButton, PowerButton #Import der Button Klassen
from VibrationSensor import Accelerometer #Import der Accelerometer Klasse

from config import * #Import aller Parameter aus der config.py



class MeasurementSystem:

    def __init__(self):
        print("="*100)
        print("Frankfurt Airport Streckenprüfer - GFA- FRAPORT AG /ZIM-TZ/FGS-IG")
        print("="*100)
        

        self.state_machine = StateMachine()

        
        self.accelerometer = Accelerometer(i2c_address=ACCELEROMETER_I2C_ADDRESS)


        self.hall_sensor = None
        if HALL_ENABLED:
            print("[HALL SENSOR] wird Initialisiert...")
            self.hall_sensor = HallSensor(pin=HALL_SENSOR_PIN, pull_up=HALL_PULL_UP, poll_hz=HALL_POLL_HZ, stable_samples=HALL_STABLE_SAMPLES)
            self.hall_sensor.reset_count()
        

        #initilisiere die Buttons
        self.begin_button = BeginButton(pin=BEGIN_BUTTON_PIN)
        #callback für Begin Button, um die Messung zu starten
        self.begin_button.set_callback(self.on_begin_button_pressed)

        self.power_button = PowerButton(pin=POWER_BUTTON_PIN)
        #callback für Power Button, um das Programm sicher zu beenden
        self.power_button.set_callback(self.on_shutdown)

        #initilisiere die LEDs
        self.idle_led = IdleLED(pin=IDLE_LED_PIN)
        self.measuring_led = MeasuringLED(pin=MEASURING_LED_PIN, blink_interval=MEASURING_LED_BLINK_INTERVAL)

        self.idle_led.turn_on() #Idle LED an, um Bereitschaft anzuzeigen
        self.copy_led = CopyLED(pin=USB_COPY_LED_PIN, blink_interval=USB_COPY_LED_BLINK_INTERVAL)
        self.copy_led.set_idle() #Copy LED aus, da noch nicht kopiert wird

        self.running = True #Flag, um die Hauptschleife zu steuern
        self.last_reading_time = 0 #Zeitstempel der letzten Sensorablesung
        self.readings = [] #Liste zum Speichern der Messdaten während einer Messung
        self.csv_output_path = CSV_OUTPUT_PATH #    Pfad für die Ausgabe der Messdaten als CSV-Datei    
        self.usb_copy_any = USB_COPY_ANY #Ob die Messdaten auf alle gefundenen USB-Laufwerke kopiert werden sollen
        self.usb_seen_mounts = set() #Set zum Verfolgen bereits erkannter USB-Laufwerke, um doppelte Kopien zu vermeiden
        self.last_usb_check_time = 0 #Zeitstempel der letzten Überprüfung auf neue USB-Laufwerke


    def on_begin_button_pressed(self):
        self.state_machine.toggle_measurement()
        if self.state_machine.is_measuring():
            self.readings.clear()
            self.last_reading_time = 0
            if self.hall_sensor:
                self.hall_sensor.reset_count()
            
            slef.idle_led.turn_off()
        else:
            self.measuring_led.turn_off()
            self.idle_led.turn_on()
            self.save_readings_to_csv()


    
    def read_vibration(self):

        try: 
            accel_data = self.accelerometer.read()
            spin_count = self.hall_sensor.get_count() if self.hall_sensor else 0

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.readings.append(
                {
                'timestamp': timestamp,
                'x': accel_data['x'],
                'y': accel_data['y'],
                'z': accel_data['z'],
                'spin_count': spin_count
                }
            )
            print(
                f"[{timestamp}] Vibration - "
                f"X={accel_data['x']} m/s², "
                f"Y={accel_data['y']} m/s², "
                f"Z={accel_data['z']} m/s²"
            )
            if self.hall_sensor:
                print(f"[{timestamp}] spins = {spin_count}") 
        
        except Exception as e:
            print(f"[ERROR] Fehler beim Lesen der Sensoren: {e}")

     
    #CSV funktionen zum Speichern der Messdaten
    def _is_removable_mount(self, device, fstype, mount_point):
        if not device.startswith("/dev/sd") or fstype in ("tmpfs", "devtmpfs"):
            return False
        if fstype not in ("vfat", "exfat", "ntfs", "ext4"):
            return False
        return mount_point.startswith("/media/") or mount_point.startswith("/mnt/")




      


