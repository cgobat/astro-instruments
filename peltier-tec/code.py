# circuitpython
# Author: Caden Gobat (@cgobat)

import time
import board
import pwmio
import analogio
import neopixel

TARGET_TEMP = 10.0 # deg C

tmp_36gz = analogio.AnalogIn(board.A0)

# mosfet_pwm = pwmio.PWMOut(board.A1)
# mosfet_pwm.frequency = 24 # Hz

neopix = neopixel.NeoPixel(board.NEOPIXEL, 1, auto_write=False)
neopix.brightness = 0.2

def getTemp(sensor: analogio.AnalogIn):
    '''Return analog temperature sensor readout in degrees Celsius'''
    voltage = sensor.value * sensor.reference_voltage / 65535
    v_to_t = lambda v: 25.0 + (v-0.750)/0.01
    return v_to_t(voltage)


while True:
    t = getTemp(tmp_36gz)
    if t >= TARGET_TEMP:
        neopix.fill((200, 10, 0)) # red
    else:
        neopix.fill((0, 40, 200)) # blue
    neopix.show()
    time.sleep(1.) # update every ~1 sec
