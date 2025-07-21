import sensor
import dial

SENSOR = 1
DIAL = 2

MODE = DIAL
# 02025-07-18 20:29:31
if __name__ == "__main__":
    if MODE == DIAL:
        dial.main_loop()
    elif MODE == SENSOR:
        sensor.main_loop()