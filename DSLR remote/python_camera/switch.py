from machine import Pin
import time

led_R = Pin(17, Pin.OUT)
led_G = Pin(16, Pin.OUT)
led_B = Pin(25, Pin.OUT)
for color in (led_R,led_G,led_B):
    color.value(1)
switch = Pin(3, Pin.IN, Pin.PULL_UP)

prevState = 1
clockSet = False

while True:
    shutterState = switch.value()
    if shutterState != prevState:
        if not clockSet:
            startTime = time.time()
            clockSet = True
        led_B.value(shutterState)
        print(f"At time {time.time()-startTime}, LED is {1-shutterState}")
        prevState = shutterState