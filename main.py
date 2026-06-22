import sensor
import dial
import machine
import utime

SENSOR = 1
DIAL = 2

MODE = SENSOR

led = machine.Pin("LED", machine.Pin.OUT)
led.toggle()
for i in range(20):
    utime.sleep(0.1)
    led.toggle()
    utime.sleep(0.2)


# 02025-07-18 20:29:31
if __name__ == "__main__":
    if MODE == DIAL:
        dial.main_loop()
    elif MODE == SENSOR:
        sensor.main_loop()