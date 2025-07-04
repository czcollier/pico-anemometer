from sinewave_generator import SinewaveGenerator
from frequency_counter import FrequencyCounter
from moving_average import MovingAverage
from utime import sleep
import time
import random

swg = SinewaveGenerator(5, 0, 10000)
fc = FrequencyCounter(1, -1, 1000)
ma = MovingAverage(20)
freq = 1000

print('starting')
for i in range(5000):
  curr_ms = time.ticks_ms()
  pt = swg.generate_sine_wave_point(freq)
  fc.update(curr_ms, pt)
  ma.add_value(fc.get_frequency())
  if i % 50 == 0:
    print(f"{fc.get_frequency():.2f},{ma.get_average():2f}")
    freq += 3 * random.randint(-1, 4)
  time.sleep_ms(10)