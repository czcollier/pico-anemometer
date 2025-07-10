# Save this file as "machine.py" in your project folder on your Linux machine.
# It now includes mocks for Pin, ADC, and RTC.

import time
import math
import random
import sinewave_generator

swg = sinewave_generator.SinewaveGenerator(1, 0, 1000)
mock_data = sinewave_generator.SinewaveGenerator(5, 0, 1000)

# --- Mock Pin Class ---
# Needed so that `machine.Pin()` doesn't cause an error.
class Pin:
    IN = 1
    OUT = 2
    def __init__(self, id, mode=-1, pull=-1):
        # This is a mock, so we don't need to do anything.
        # The print statement is helpful for debugging.
        print(f"MockPin: Pin {id} initialized.")
    def value(self, val=None):
        # Return a dummy value if called.
        freq = mock_data.generate_sine_wave_point(0.3)
        sw_value = swg.generate_sine_wave_point(freq)
        return 0 if sw_value < 0 else 1

# --- Mock ADC Class ---
class ADC:
    """
    This is a mock ADC class that generates a simulated sine wave
    to mimic the output of the anemometer for local testing.
    """
    def __init__(self, pin):
        print(f"MockADC: Initialized on virtual pin {pin}.")
        self._start_time = time.time()
        self._active = False
        self._last_read  = time.ticks_ms()
        self._init_freq = 5
        self._curr_freq = self._init_freq

    def read_u16(self):
        """
        Generates the next point in a simulated sine wave.
        Returns an integer value between 0 and 65535.
        """
        # --- Simulation Parameters (You can change these) ---
        amplitude = 5000  # The peak of the wave (max 32767)
        noise_level = 300 # How much random noise to add
        offset = 32000 # Center the wave in the middle of the 0-65535 range
        curr_ms = time.ticks_ms()
        if (curr_ms - self._last_read > 3000):
            #rnd_ws_offset = 3
            rnd_ws_offset = random.randint(0, 2)
            print(f"changing freq: {rnd_ws_offset}")
            self._curr_freq += rnd_ws_offset
            self._last_read = curr_ms

        elapsed_time = time.time() - self._start_time
        angle = 2 * math.pi * self._curr_freq * elapsed_time
        sine_value = amplitude * math.sin(angle)
        noise = random.randint(-noise_level, noise_level)
        if not self._active:
            return noise
        else:
            final_value = int(offset + sine_value + noise)
            # Clamp the value to the u16 range
            return max(0, min(65535, final_value))

# --- Mock RTC Class (NEW) ---
class RTC:
    """
    This is a mock RTC class that uses the host system's time.
    """
    def __init__(self):
        print("MockRTC: Initialized.")

    def datetime(self, dt=None):
        """
        Returns a tuple with the current date and time, matching the
        format of the Pico's RTC.
        Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        """
        if dt is None:
            # Get the current time from the host OS
            now = time.localtime()
            # The Pico's weekday is 1-7 (Mon-Sun), Python's is 0-6 (Mon-Sun)
            weekday = now.tm_wday + 1
            # Return the tuple in the expected format
            return (now.tm_year, now.tm_mon, now.tm_mday, weekday, 
                    now.tm_hour, now.tm_min, now.tm_sec, 0)
        else:
            # This part would handle setting the time, but we don't need it for mocking.
            print("MockRTC: Setting time (not implemented in mock).")
            return None

