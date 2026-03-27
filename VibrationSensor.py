import smbus 
import time 
from abc import ABC, abstractmethod
class Sensor(ABC):
    @abstractmethod
    def read(self):
        raise NotImplementedError

class Accelerometer(Sensor):


    #Registers des Beschleunigungssensors
    #detektierte Addresse vom raspian befehl i2cdetect -y 1 beim Anschließen des Sensors
    WHO_AM_I = 0x0D 
    CTRL_REG1 = 0x2A 
    OUT_X_MSB = 0x01
    XYZ_DATA_CFG = 0x0E

    def __init__(self, i2c_address=0x1D, bus=1, auto_detect=True):
        
        self.bus= bus 
        self.i2c_address = i2c_address

        self.i2c = smbus.SMBus(bus)
        
        who = self.i2c.read_byte_data(self.i2c_address, self.WHO_AM_I)
    
        self._standby()
        self._set_range_8g()
        self._active()

        print(f"[ACCELEROMETER] Initialized on bus {bus}, address 0x{self.i2c_address:02X}")


  
    def _standby(self):
        ctrl = self.i2c.read_byte_data(self.i2c_address, self.CTRL_REG1)
        self.i2c.write_byte_data(self.i2c_address, self.CTRL_REG1, ctrl & ~0x01)   
        time.sleep(0.05)
        print("[ACCELEROMETER] Standby mode activated")
    

    def _active(self):
        ctrl = self.i2c.read_byte_data(self.i2c_address, self.CTRL_REG1)
        self.i2c.write_byte_data(self.i2c_address, self.CTRL_REG1, ctrl | 0x01)   
        time.sleep(0.05)
        print("[ACCELEROMETER] Active mode activated")

    def _set_range_8g(self):
        self.i2c.write_byte_data(self.i2c_address, self.XYZ_DATA_CFG, 0x02) 
        time.sleep(0.05)
        print("[ACCELEROMETER] Range set to ±8g")
    
    @staticmethod
    def _convert_14bit(msb, lsb):
        raw = (msb << 8) | lsb
        raw = raw >> 2
        if raw > 8191:
            raw -= 16384
        return raw

    def read(self):

        if self.i2c is None:
            return {'x': 999, 'y': 999, 'z': 999}
        
        #6 Bytes lesen: X_MSB, X_LSB, Y_MSB, Y_LSB, Z_MSB, Z_LSB
        try: 
            data = self.i2c.read_i2c_block_data(self.i2c_address, self.OUT_X_MSB, 6)

            x_raw = self._convert_14bit(data[0], data[1])
            y_raw = self._convert_14bit(data[2], data[3])   
            z_raw = self._convert_14bit(data[4], data[5]) 


            x = (x_raw/ 1024.0) * 9.81
            y = (y_raw/ 1024.0) * 9.81
            z = (z_raw/ 1024.0) * 9.81  

            return {'x': round(x, 2), 'y': round(y, 2), 'z': round(z, 2)}
        
        except OSError as e:
            print(f"[ACCELEROMETER] Read OSError (errno={getattr(e, 'errno', 'N/A')}): {e}")
            return {'x': 999, 'y': 999, 'z': 999}