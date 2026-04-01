#dieses Modul dient der Klassen der Hall-Sensoren. Ziel dabei ist, eine simple Inkeremtierung einer Varaible zu sichern. 
import threading 
import time 
from abc import ABC, abstractmethod
import RPi.GPIO as GPIO

class HallSensor(ABC):
    def __init__(self, pin, pull_up=True, poll_hz=800, stable_samples=5):
        self.pin = pin
        self.pull_up = pull_up
        self.poll_hz = poll_hz
        self.stable_samples = max(1, stable_samples)

        self.GPIO = GPIO
        self._count = 0
        # _count wird vom Hintergrund-Thread geschrieben und vom Hauptthread gelesen.
        self._lock = threading.Lock()
        # Dieses Event dient als Stop-Signal, damit der Thread sauber beendet werden kann.
        self._stop = threading.Event()
        self._thread = None
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        try:
            GPIO.cleanup(self.pin)  # Clean up in case it was used before
        except Exception: 
            pass 

        pull = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull)
        
        # Eigener Daemon-Thread fuer kontinuierliches Polling, ohne die Hauptschleife zu blockieren.
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    
    def _run(self):
        period = 1.0 / self.poll_hz if self.poll_hz > 0 else 0.01
        armed = True 
        high_streak = 0
        last = self.GPIO.input(self.pin)

        while not self._stop.is_set():
              cur = self.GPIO.input(self.pin)

              if armed: 
                     if cur == 1 and last == 0:
                        high_streak += 1
                        if high_streak >= self.stable_samples:
                            # Zaehlerzugriff absichern, damit Lesen und Schreiben zwischen Threads konsistent bleiben.
                            with self._lock:
                                self._count += 1
                            armed = False 
                            high_streak = 0 
                    else:
                        high_streak = 0
              else:
                  if cur == 1:
                        high_streak += 1
                        if high_streak >= self.stable_samples:
                            armed = True 
                            high_streak = 0
                  else:
                        high_streak = 0
              
              last = cur
              time.sleep(period)
    
    def get_count(self):
         with self._lock:
              return self._count
    
    def reset_count(self):
        with self._lock:
            self._count = 0

    def cleanup(self):
        # Erst Stop-Signal setzen, dann kurz auf das Ende des Threads warten.
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        
        if self.GPIO is None: 
            return
        
        self.GPIO.cleanup(self.pin)
                
