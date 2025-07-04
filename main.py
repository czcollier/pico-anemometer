import time
import machine
import math
from frequency_counter import FrequencyCounter
from moving_average import MovingAverage
import google_auth
import czc_wifi
import secrets
import urequests
import _thread

# --- Configuration ---
ADC_PIN = 26
# This threshold should be set above your noise level (~4000)
# and below the peak signal when spinning. Start with 10000 and adjust.
PULSE_THRESHOLD_HIGH = 8000
PULSE_THRESHOLD_LOW = 800
SMOOTHING_WINDOW_SIZE = 20
FREQUENCY_COUNTER_TIMEOUT = 1000
FBASE_URL_FMT = "https://pound-weather-default-rtdb.firebaseio.com/sensors.json?access_token={access_token}"
   
    # --- Initialization ---
ADC = machine.ADC(ADC_PIN)

# Core 1: The Sensor Reading Loop
# This function will run continuously on the second core.
def sensor_loop():
    global latest_smoothed_frequency
    
    # sensor initialization (specific to sensor loop core)
    adc = machine.ADC(26)
    
    # --- Auto-Tuning ---
    print("Core 1: Auto-tuning threshold...")
    noise_ceiling = 0
    noise_floor = 65535

    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        reading = adc.read_u16()
        if reading > noise_ceiling: noise_ceiling = reading
        if reading < noise_floor: noise_floor = reading
        time.sleep_ms(10)
    
    high_noise_threshold = noise_ceiling + 2000
    low_noise_threshold = noise_ceiling
    print(f"Core 1: High threshold set to {high_noise_threshold}, Low set to {low_noise_threshold}")
    
    fc = FrequencyCounter(
        high_noise_threshold,
        low_noise_threshold,
        FREQUENCY_COUNTER_TIMEOUT)
    
    smoother = MovingAverage(SMOOTHING_WINDOW_SIZE)
    
    print("Core 1: Starting sensor reading loop.")
    while True:
        current_time = time.ticks_ms()
        sensor_value = adc.read_u16()

        fc.update(current_time, sensor_value)
        current_frequency = fc.get_frequency()
        smoother.add_value(current_frequency)
        
        # --- safely update the shared variable ---
        with data_lock:
            latest_smoothed_frequency = smoother.get_average()
            
        time.sleep_ms(10) 

# ==============================================================================
# Core 0: The Main Program (Network, Firebase, etc.)
# ==============================================================================
def send_to_firebase(frequency_hz, access_token):
    try:
        data_to_send = {'wind_speed': round(frequency_hz, 2)}
        print(f"Core 0: Sending to Firebase: {data_to_send}")
        response = urequests.patch(
            FBASE_URL_FMT.format(access_token=access_token),
            json=data_to_send)
        print(f"Core 0: Firebase response: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"Core 0: Error sending to Firebase: {e}")

# ==============================================================================
# Global variable to share data between cores and a Lock to protect it
# ==============================================================================
latest_smoothed_frequency = 0.0
data_lock = _thread.allocate_lock()

last_reading = 0

if __name__ == "__main__":
    # --- Start the sensor loop on the second core ---
    _thread.start_new_thread(sensor_loop, ())

    # --- Connect to Wi-Fi on the main core ---
    czc_wifi.connect_wifi(secrets.WIFI_SSID, secrets.WIFI_PASS)

    gcp_access_token = google_auth.get_gcp_access_token()

    # --- Main loop for Core 0 ---
    while True:
        # --- Safely read the shared variable ---
        with data_lock:
            current_reading = latest_smoothed_frequency
            
        # --- Send the data to Firebase ---
        if not math.isclose(current_reading, last_reading, abs_tol=0.05) and current_reading >= 0:
            send_to_firebase(current_reading, gcp_access_token)
        
        last_reading = current_reading
        # NB in seconds not ms 
        time.sleep(1)
