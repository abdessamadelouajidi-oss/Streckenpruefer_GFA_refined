"Button des PCB Steuerungsplatine" 

import time
import threading
import RPi.GPIO as GPIO
"father class for all buttons, handles GPIO"
class Button: 
    def __init__(self, pin, name, pull_up=True):
        self.pin = pin
        self.name = name
        self.pull_up = pull_up
        self.callback = None
        self.GPIO=GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        pull = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN 


    def set_callback(self, callback):
        self.callback = callback
    
    def is_pressed(self):
        if self.GPIO is None:
            return False
        try:            
            state = self.GPIO.input(self.pin)
            return state == 0 if self.pull_up else state == 1
        except Exception:
            return False
    


class BeginButton(Button):

    def __init__(self, pin=17, name="BEGIN_BUTTON"):
        super().__init__(pin, name, pull_up=True)
        self.last_press_time = 0
        self.debounce_time = 0.3
        

    def check_press(self):
       

        # Re-arm only after button release
        if not self.is_pressed():
            self._armed = True
            return False

        current_time = time.time()
        if self._armed and (current_time - self.last_press_time > self.debounce_time):
            self.last_press_time = current_time
            print(f"[{self.name}] Pressed - toggling measurement")
            if self.callback:
                self.callback()
            return True

        return False 

class PowerButton(Button):
    def __init__(self, pin=27, name="POWER_BUTTON"):
        super().__init__(pin, name, pull_up=True)
        self.hold_threshold = 2.0
        self.press_start_time = None
        self.shutdown_callback = None
        
    
    def check_hold(self): 
        if self.is_pressed():
            if self.press_start_time is None:
                self.press_start_time = time.time()
                print(f"[{self.name}] Pressed (hold for {self.hold_threshold}s to shutdown)")
            
            hold_time = time.time() - self.press_start_time
            if hold_time >= self.hold_threshold:
                print(f"[{self.name}] Held for {round(hold_time, 2)}s - Stopping measurement...")
               
                if self.shutdown_callback:
                    self.shutdown_callback()
                self.press_start_time = None
                return True
        
        else:
            if self.press_start_time is not None:
                hold_time = time.time() - self.press_start_time
                if hold_time <= self.hold_threshold:
                    print(f"[{self.name}] Released after {round(hold_time, 2)}s (not long enough)")
                    self.press_start_time = None
                    
                    
        return False