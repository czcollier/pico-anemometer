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

from machine import ADC

# --- Configuration ---
ADC_PIN = 26
SMOOTHING_WINDOW_LEN_MS = 1000
FREQUENCY_COUNTER_TIMEOUT = 1000
FBASE_URL_FMT = "https://{db_name}.firebaseio.com/{path}?access_token={access_token}"

SAMPLING_INTERVAL = 10
READING_TOLERANCE = 0.05

REPORTING_INTERVAL_MS = 1 * 1000
AUTH_TOKEN_EXPIRY_MS = 3600 * 1000
AUTH_REFRESH_INTERVAL_MS = int(AUTH_TOKEN_EXPIRY_MS * 0.9)

SMOOTHING_WINDOW_SIZE = int(SMOOTHING_WINDOW_LEN_MS / SAMPLING_INTERVAL)

def auto_tune_noise_threshold(adc: ADC) -> tuple[int, int]:
    # --- Auto-Tuning ---
    print("Core 1: Auto-tuning threshold...")
    noise_ceiling: int = 0
    noise_floor: int = 65535

    start_time: int = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        reading: int = adc.read_u16()
        if reading > noise_ceiling: noise_ceiling = reading
        if reading < noise_floor: noise_floor = reading
        time.sleep_ms(10)
    
    high_noise_threshold = noise_ceiling + 2000
    low_noise_threshold = noise_ceiling

    return high_noise_threshold, low_noise_threshold


# Core 1: The Sensor Reading Loop
# This function will run continuously on the second core.
def sensor_loop() -> None:
    global latest_smoothed_frequency
    
    # sensor initialization (specific to sensor loop core)
    adc:ADC = machine.ADC(26)
    
    (high_noise_threshold, low_noise_threshold) = auto_tune_noise_threshold(adc)

    print(f"sensor core: noise thresholds set.  high: "
    f"{high_noise_threshold}, low: {low_noise_threshold}")
    
    frequency_counter = FrequencyCounter(
        high_noise_threshold,
        low_noise_threshold,
        FREQUENCY_COUNTER_TIMEOUT)
    
    smoother = MovingAverage(SMOOTHING_WINDOW_SIZE)
    sensor_debug_interval_ms = 500 
    last_sensor_debug = 0

    print("sensor core: Starting sensor reading loop.")
    while True:
        current_time: int = time.ticks_ms()
        sensor_value: int = adc.read_u16()
        frequency_counter.update(current_time, sensor_value)
        current_frequency: float = frequency_counter.get_frequency()
        smoother.add_value(current_frequency)
        
        # --- safely update the shared variable ---
        with data_lock:
            latest_smoothed_frequency = smoother.get_average()
        
        if time.ticks_diff(current_time, last_sensor_debug) >= sensor_debug_interval_ms:
            last_sensor_debug = current_time
            #print(f"raw: {sensor_value:0.2f}") 
            #print(f"freq: {current_frequency:0.2f}") 
            #print(f"smooth: {latest_smoothed_frequency:0.2f}") 

        time.sleep_ms(SAMPLING_INTERVAL) 

def send_to_firebase(frequency_hz: float, db_name: str, path: str, access_token: str) -> None:
    try:
        freq_rounded = round(frequency_hz, 2)
        data_to_send = {"wind_speed": freq_rounded }
        print(f"sending to Firebase: {data_to_send}")

        fbase_url = FBASE_URL_FMT.format(
            access_token=access_token,
            db_name=db_name, path=path)

        response = urequests.patch(
            url=fbase_url,
            json=data_to_send)
        print(f"firebase response: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"error sending to Firebase: {e}")

# Global variable to share data between cores and a Lock to protect it
latest_smoothed_frequency: float = 0.0
data_lock = _thread.allocate_lock()


# main core: network, firebase, etc
if __name__ == "__main__":
    # --- Start the sensor loop on the second core ---
    _thread.start_new_thread(sensor_loop, ())

    # --- Connect to Wi-Fi on the main core ---
    czc_wifi.connect_wifi(secrets.WIFI_SSID, secrets.WIFI_PASS)

    gcp_access_token = google_auth.get_gcp_access_token()
    start_ms = time.ticks_ms()
    last_auth_refresh_time = start_ms
    last_report_time = start_ms - REPORTING_INTERVAL_MS
    last_reading = 0

    print("main core: startng main network loop")

    # --- Main loop for Core 0 ---
    while True:
        curr_ms = time.ticks_ms()
        if time.ticks_diff(curr_ms, last_report_time) >= REPORTING_INTERVAL_MS:
            last_report_time = curr_ms
            # safely read shared state
            with data_lock:
                current_reading = abs(latest_smoothed_frequency)
            # don't send values very similar to the last reading
            print(f"reading: {current_reading:0.2f}")
            if not math.isclose(current_reading, last_reading, abs_tol=READING_TOLERANCE):
                send_to_firebase(
                    current_reading,
                    secrets.FIREBASE_DB_NAME,
                    secrets.FIREBASE_DATA_PATH, 
                    gcp_access_token)
        
            last_reading = current_reading

            auth_ttl = int((AUTH_REFRESH_INTERVAL_MS
                - time.ticks_diff(curr_ms, last_auth_refresh_time)) / 1000)
            
            print(f"auth ttl: {auth_ttl}") 
        if  auth_ttl <= 0:
            last_auth_refresh_time = curr_ms
            access_token = google_auth.get_gcp_access_token()
    
        time.sleep_ms(100)
