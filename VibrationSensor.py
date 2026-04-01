import smbus
import time
from abc import ABC, abstractmethod


class Sensor(ABC):
    @abstractmethod
    def read(self):
        raise NotImplementedError


class Accelerometer(Sensor):
    # Registers des Beschleunigungssensors
    # Detektierte Adresse vom Raspberry-Pi-Befehl `i2cdetect -y 1`
    WHO_AM_I = 0x0D
    CTRL_REG1 = 0x2A
    OUT_X_MSB = 0x01
    XYZ_DATA_CFG = 0x0E

    # MMA8452Q sensitivity at +/-8g
    COUNTS_PER_G_8G = 256.0

    def __init__(self, i2c_address=0x1D, bus=1, auto_detect=False):
        self.bus = bus
        self.i2c_address = i2c_address
        self.counts_per_g = self.COUNTS_PER_G_8G

        self.i2c = smbus.SMBus(bus)
        self.device_id = self.i2c.read_byte_data(self.i2c_address, self.WHO_AM_I)

        self._standby()
        self._set_range_8g()
        self._active()

        print(
            f"[ACCELEROMETER] Initialized on bus {bus}, "
            f"address 0x{self.i2c_address:02X}, id 0x{self.device_id:02X}"
        )

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
        print("[ACCELEROMETER] Range set to +/-8g")

    @staticmethod
    def _convert_12bit(msb, lsb):
        # MMA8452Q outputs signed 12-bit values left-aligned in the MSB/LSB pair.
        raw = ((msb << 8) | lsb) >> 4
        if raw > 2047:
            raw -= 4096
        return raw

    def read(self):
        if self.i2c is None:
            return {"ax": 999, "ay": 999, "az": 999}

        # 6 Bytes lesen: X_MSB, X_LSB, Y_MSB, Y_LSB, Z_MSB, Z_LSB
        try:
            data = self.i2c.read_i2c_block_data(self.i2c_address, self.OUT_X_MSB, 6)

            x_raw = self._convert_12bit(data[0], data[1])
            y_raw = self._convert_12bit(data[2], data[3])
            z_raw = self._convert_12bit(data[4], data[5])

            ax = (x_raw / self.counts_per_g) * 9.81
            ay = (y_raw / self.counts_per_g) * 9.81
            az = (z_raw / self.counts_per_g) * 9.81

            return {"ax": round(ax, 2), "ay": round(ay, 2), "az": round(az, 2)}

        except OSError as e:
            print(f"[ACCELEROMETER] Read OSError (errno={getattr(e, 'errno', 'N/A')}): {e}")
            return {"ax": 999, "ay": 999, "az": 999}
