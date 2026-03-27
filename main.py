#Das Projekt wird mit Python 3.10.6 erstellt und getestet. Es könnte sein, dass es mit anderen Versionen nicht funktioniert.
#Das Projekt wird später für die Bewrtung auf GitHub verföffentlicht.
import RPi.GPIO as GPIO
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
        
        print("Initializing buttons...")
        #initilisiere die Buttons
        self.begin_button = BeginButton(pin=BEGIN_BUTTON_PIN)
        #callback für Begin Button, um die Messung zu starten
        self.begin_button.set_callback(self.on_begin_button_pressed)

        self.power_button = PowerButton(pin=POWER_BUTTON_PIN)
        #callback für Power Button, um das Programm sicher zu beenden
        self.power_button.set_shutdown_callback(self.on_shutdown)

        #initilisiere die LEDs
        self.idle_led = IdleLED(pin=IDLE_LED_PIN)
        self.measuring_led = MeasuringLED(pin=MEASURING_LED_PIN, blink_interval=MEASURING_LED_BLINK_INTERVAL)

        self.idle_led.turn_on() #Idle LED an, um Bereitschaft anzuzeigen
        self.usb_copy_led = CopyLED(pin=USB_COPY_LED_PIN, blink_interval=USB_COPY_LED_BLINK_INTERVAL)
        self.usb_copy_led.set_idle() #Copy LED aus, da noch nicht kopiert wird

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
            # NEU: nur neue Werte ab Start
            self.readings.clear()
            self.last_reading_time = 0
            if self.hall_sensor:
                self.hall_sensor.reset_count()

            self.idle_led.turn_off()
        else:
            self.measuring_led.turn_off()
            self.idle_led.turn_on()
            # optional: hier NICHT leeren, sonst verlierst du Messdaten beim Stop per BEGIN
            # self.readings.clear()

    def on_shutdown(self):

        if self.state_machine.is_measuring():
            self.state_machine.stop_measurement()

        self.measuring_led.turn_off()
        self.idle_led.turn_on()
        self.save_readings_to_csv()

    # IMPORTANT: do NOT clear readings here,
    # otherwise USB copy later will say "No readings to copy yet."
    # self.readings.clear()

        print("\n[POWER] Measurement stopped. Returned to IDLE.")


    
    def read_vibration(self):

        try: 
            accel_data = self.accelerometer.read()
            spin_count = self.hall_sensor.get_count() if self.hall_sensor else 0

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.readings.append(
                {
                'timestamp': timestamp,
                'ax': accel_data['x'],
                'ay': accel_data['y'],
                'az': accel_data['z'],
                'spin_count': spin_count
                }
            )
            print(
                f"[{timestamp}] Vibration - "
                f"X={accel_data['ax']} m/s², "
                f"Y={accel_data['ay']} m/s², "
                f"Z={accel_data['az']} m/s²"
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

    def _scan_usb_mounts(self):
        if not self.usb_copy_any:
            return []
        mounts = set()
        try:
            with open("/proc/mounts", "r") as mounts_file:
                for line in mounts_file:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    device, mount_point, fstype = parts[0], parts[1], parts[2]
                    if self._is_removable_mount(device, fstype, mount_point):
                        mounts.add(mount_point)
        
        except Exception as e:
            print(f"[ERROR] Fehler beim Lesen von /proc/mounts: {e}")
        return sorted(mounts)             

    
    def _build_usb_csv_path(self, mount_path):

        base = os.path.splitext(os.path.basename(self.csv_output_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        return os.path.join(mount_path, f"{base}_{timestamp}.csv")        

    def _copy_csv_to_mounts(self, mount_paths):
        
        if not self.readings:
            print("[COPY] Keine Messdaten zum Kopieren vorhanden.")
            return
        
        self.usb_copy_led.set_copying()
        self.save_readings_to_csv()  # Speichern der aktuellen Messdaten vor dem Kopieren

        success = False  #Flag, um den Erfolg des Kopiervorgangs zu verfolgen

        for mount_path in mount_paths: 

            try: 
                usb_csv_path = self._build_usb_csv_path(mount_path)
                shutil.copy2(self.csv_output_path, usb_csv_path)
                success = True
            except Exception as e:
                print(f"[ERROR] Fehler beim Kopieren der CSV auf {mount_path}: {e}")

        if success:
            self.usb_copy_led.set_copied()
        else:
            self.usb_copy_led.set_idle()

    def _check_usb_copy(self):
        mounts = set(self._scan_usb_mounts())
        new_mounts = mounts - self.usb_seen_mounts

        if new_mounts:
            self._copy_csv_to_mounts(new_mounts)
        
        self.usb_seen_mounts = mounts

        if mounts:
            self.usb_copy_led.set_copied()
        else:
            self.usb_copy_led.set_idle()




    def run(self):
        try: 
            while self.running: 
                self.begin_button.check_press()
                self.power_button.check_hold()


                if self.state_machine.is_measuring():
                    self.measuring_led.update()
                self.usb_copy_led.update()


                current_time = time.time()
                if (
                    self.state_machine.is_measuring() and 
                    current_time - self.last_reading_time >= READING_INTERVAL
                ):
                    self.read_vibration()
                    self.last_reading_time = current_time
                
                if current_time - self.last_usb_check_time >= USB_CHECK_INTERVAL:
                    self.last_usb_check_time = current_time
                    self._check_usb_copy()

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Messsystem wird sicher heruntergefahren...")
            self.on_shutdown()
        finally:
            self.cleanup()

    def save_readings_to_csv(self):
        if not self.readings: 
            print("[CSV] no readings to save")
            return
        try: 
            with open(self.csv_output_path, "w", newline= "") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames = ["timestamp", "ax" , "ay" , "az" , "spin_count"],)
                writer.writeheader()
                writer.writerows(self.readings)
            print (f"[CSV] Saved {len(self.readings)} readings to {self.csv_output_path}")
        
        except Exception as e : 
            print(f"[CSV] Failed to write CSV file: {e}")
        
    def cleanup(self):
        print("cleaning up ...")
        if self.hall_sensor:
            self.hall_sensor.cleanup()
        GPIO.cleanup()
        print("GPIO ist clean!")

        self.save_readings_to_csv()



def main():

    system = MeasurementSystem()
    system.run()


if __name__ == "__main__":
    main()
        






      


