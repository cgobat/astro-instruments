# circuitpython
# Author: Caden Gobat (@cgobat)

import os
import time
import board, microcontroller
import analogio, digitalio, pwmio, displayio
import neopixel
from adafruit_displayio_ssd1306 import SSD1306

displayio.release_displays() # reset/release any currently configured display(s)

EPOCH = time.mktime(time.struct_time((2020, 1, 1, 0, 0, 0, -1, -1, -1)))
TARGET_TEMP = 10.0 # deg C

I2C = board.I2C() # create I2C bus
display_bus = displayio.I2CDisplay(I2C, device_address=0x3C) # initalize display driver over I2C
display = SSD1306(display_bus, width=128, height=64) # instantiate display control object itself

tmp_36gz = analogio.AnalogIn(board.A0) # analog input pin connected to temperature sensor

mosfet_pwm = pwmio.PWMOut(board.A1, variable_frequency=True) # analog output pin for PWM control
mosfet_pwm.frequency = 100 # Hz

neopix = neopixel.NeoPixel(board.NEOPIXEL, 1, auto_write=False) # built-in RGB LED
neopix.brightness = 0.2 # 20% brightness

def getTemp(sensor: analogio.AnalogIn):
    '''Returns temperature in °C based on analog sensor readout.
    Assumptions:
      - Raw ADC value is out of 16 bits
      - Conversion slope is 10 mV/°C
      - Sensor reading is 750 mV at 25 °C'''
    voltage = sensor.value * sensor.reference_voltage / 65535
    v_to_t = lambda v: 25.0 + (v-0.750)/0.01
    return v_to_t(voltage)

def isoformat(time_struct = None, doy = False) -> str:
    if time_struct is None: # if no input, use current time
        time_struct = time.localtime()
    if isinstance(time_struct, (int, float)):
        time_struct = time.localtime(time_struct)
    if doy:
        _date = f"{time_struct.tm_year:04d}-{time_struct.tm_yday:03d}"
    else:
        _date = f"{time_struct.tm_year:04d}-{time_struct.tm_mon:02d}-{time_struct.tm_mday:02d}"
    _time = f"{time_struct.tm_hour:02d}:{time_struct.tm_min:02d}:{time_struct.tm_sec:02d}"
    return f"{_date}T{_time}"


if __name__ == "__main__":
    while True:
        t = getTemp(tmp_36gz) # read temperature from sensor
        print(f"t: {time.time()-EPOCH}s / T: {t:.1f} C", end="\r")
        if t >= TARGET_TEMP:
            neopix.fill((200, 10, 0)) # red
        else:
            neopix.fill((0, 40, 200)) # blue
        neopix.show()
        time.sleep(1.) # update every ~1 sec
