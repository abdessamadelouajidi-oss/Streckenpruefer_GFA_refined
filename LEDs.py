import time 
import RPi.GPIO as GPIO

class LED: 
# Ein LED hat ein GPIO Pin mit der sie verbunen ist. 
# Init funktion:
    def __init__(self, pin, name):
        self.pin = pin # GPIO Pin Nummer
        self.name = name # Name der LED, in unsremen Fall "IdleLED" "MeasuringLED" und "copyLED"
        self.is_on = False # Bei der Initialisierung zunächst einamal sind die LEDsaus
        self.GPIO = GPIO  # GPIO objekt der jeweuligen LED Klasse
        # das Modus der GPIOs wird auf BCM gesetzt, damit die Pin Nummerierung der GPIOs verwendet werden kann.
        # die GPIOs für die LED werden als Ausgang definiert und auf LOW gesetzt, damit die LEDs zunächst aus sind.
        GPIO.setmode(GPIO.BCM) 
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        
    def turn_on(self):
        if not self.is_on:
            self.GPIO.output(self.pin, self.GPIO.HIGH)
            self.is_on = True

    def turn_off(self):
        if self.is_on:
            self.GPIO.output(self.pin, self.GPIO.LOW)
            self.is_on = False


class IdleLED(LED):            

    def __init__(self, pin=5, name="IdleLED"):
        #super gibt die Möglichkeit, die Methoden der Parentklasse (LED) aufzurufen, um die Initialisierung der LED durchzuführen.
        super().__init__(pin, name)



class MeasuringLED(LED):

    def __init__(self, pin=6, name="MeasuringLED", blink_interval=0.5):
        super().__init__(pin, name)
        self.blink_interval = blink_interval
        self.last_blink_time = 0
    
    def update(self):
            current_time = time.time()
            if current_time - self.last_blink_time >= self.blink_interval:
                if self.is_on:
                    self.turn_off()
                else:
                    self.turn_on()
                self.last_blink_time = current_time



class CopyLED(LED):

    def __init__(self, pin=13, name="CopyLED", blink_interval=0.2):
        super().__init__(pin, name)
        self.blink_interval = blink_interval
        self.last_blink_time = 0
        self.mode = "off" 
    
    def set_copying(self):
        self.mode = "blinking"
    
    def set_copied(self):
        self.mode = "on"
    
    def set_idle(self):
        self.mode = "off"
        self.turn_off()
    
    def update(self):
        if self.mode == "blinking":
            current_time = time.time()
            if current_time - self.last_blink_time >= self.blink_interval:
                if self.is_on:
                    self.turn_off()
                else:
                    self.turn_on()
                self.last_blink_time = current_time
        elif self.mode == "on":
            if not self.is_on:
                self.turn_on()
        elif self.mode == "off":
            if self.is_on:
                self.turn_off()