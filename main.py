import time
import machine
import math
from frequency_counter import FrequencyCounter
from moving_average import MovingAverage
import jwt_auth
import ntp
import czc_wifi
import secrets
import urequests
import _thread

# --- Configuration ---
# sensor
SENSOR_PIN: int = 15
SENSOR_DEBUG_MODE: bool = False
SAMPLING_INTERVAL: int = 20 
SMOOTHING_WINDOW_LEN_MS: int = 1200
FREQUENCY_COUNTER_TIMEOUT: int = 5000
READING_TOLERANCE: float = 0.05
SMOOTHING_WINDOW_SIZE: int = int(SMOOTHING_WINDOW_LEN_MS / SAMPLING_INTERVAL)

# data upload
REPORTING_INTERVAL_MS: int = 1 * 1000
FIREBASE_URL_FMT: str = "https://{db_name}.firebaseio.com/{path}"
WIFI_CONNECT_SLEEP_S: int = 10

# auth
AUTH_TOKEN_EXPIRY_MS: int = 1000 * 3600
AUTH_REFRESH_INTERVAL_MS: int = int(AUTH_TOKEN_EXPIRY_MS * 0.9)
NTP_RETRIES: int = 1
NTP_FAILURE_LENIENT: bool = True


# Global data shared between cores
sensor_loop_may_proceed: bool = True
latest_smoothed_frequency: float = 0.0
# lock for latest_smoothed_frequency
data_lock = _thread.allocate_lock()


def get_google_auth_headers(access_token: str):
  return {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}"
  }


# The sensor reading loop
# This function will run continuously on the sensor core
def sensor_loop() -> None:
    global latest_smoothed_frequency
    global sensor_loop_may_proceed

    # sensor initialization (specific to sensor loop core)
    sensor_pin = machine.Pin(SENSOR_PIN, machine.Pin.IN)
    
    frequency_counter = FrequencyCounter(
        high_threshold=0.5,
        low_threshold=0.4,
        timeout_ms=FREQUENCY_COUNTER_TIMEOUT)
    
    smoother = MovingAverage(SMOOTHING_WINDOW_SIZE)

    try:
        print("sensor core: Starting sensor reading loop.")
        while sensor_loop_may_proceed:
            current_tick: int = time.ticks_ms()
            sensor_value: int = sensor_pin.value()
            frequency_counter.update(current_tick, sensor_value)
            current_frequency: float = frequency_counter.get_frequency()
            smoother.add_value(current_frequency)
            
            # --- safely update the shared variable ---
            with data_lock:
                latest_smoothed_frequency = smoother.get_average()
            time.sleep_ms(SAMPLING_INTERVAL) 
    except Exception as e:
        raise e;
    finally:
        print("sensor thread exiting")
        _thread.exit()


def connect_to_wifi() -> None:
    czc_wifi.connect_wifi(secrets.WIFI_SSID, secrets.WIFI_PASS)


def get_formatted_time() -> str:
    synced_time = time.localtime()
    return (f"{synced_time[0]}-{synced_time[1]:02d}-{synced_time[2]:02d}"
          f" {synced_time[3]:02d}:{synced_time[4]:02d}:{synced_time[5]:02d}")


def google_jwt_authenticate(ntp_failure_lenient: bool=False):
    time_synced = ntp.sync_clock_to_ntp()

    if not time_synced:
        print("error: Could not sync time with NTP after multiple attempts.")
        if not ntp_failure_lenient:
            print("Cannot proceed without accurate time.")
            return None
        else:
            print("continuing without syncing time to ntp and hoping for the best")

    return jwt_auth.get_jwt_access_token()


def send_to_firebase(
        frequency_hz: float,
        timestamp: str,
        db_name: str, path: str,
        access_token: str) -> None:
    try:
        freq_rounded = round(frequency_hz, 2)
        data_to_send = {
            "wind_speed": freq_rounded,
            "timestamp": timestamp
        }

        print(f"sending to Firebase: {data_to_send}")

        fbase_url = FIREBASE_URL_FMT.format(db_name=db_name, path=path)
        fbase_headers = get_google_auth_headers(access_token)
        response = urequests.patch(
            url=fbase_url,
            headers=fbase_headers,
            json=data_to_send)
        print(f"firebase response: {response.status_code}\n{response.text}")
        response.close()
    except Exception as e:
        print(f"error sending to Firebase: {e}")


def main_loop() -> None:
    global sensor_loop_may_proceed
    try:
        # --- Start the sensor loop on the second core ---
        _thread.start_new_thread(sensor_loop, ())

        # --- Connect to Wi-Fi on the main core ---
        connect_to_wifi()

        gcp_access_token = google_jwt_authenticate(NTP_FAILURE_LENIENT)
        start_ms = time.ticks_ms()
        last_auth_refresh_time = start_ms
        last_report_time = start_ms - REPORTING_INTERVAL_MS
        last_reading = 0

        print("main core: startng main network loop")

        # --- main loop for main core ---
        while True:
            curr_ms = time.ticks_ms()
            # CONNECTION WATCHDOG: Check if we are still connected.
            if not czc_wifi.is_wifi_connected():
                print("main core: Wi-Fi connection lost. Attempting to reconnect...")
                connect_to_wifi() 
                time.sleep(WIFI_CONNECT_SLEEP_S)
                continue # skip the rest of this loop iteration

            auth_ttl = int((AUTH_REFRESH_INTERVAL_MS
                - time.ticks_diff(curr_ms, last_auth_refresh_time)) / 1000)

            if  auth_ttl <= 0:
                gcp_access_token = google_jwt_authenticate(NTP_FAILURE_LENIENT)
                last_auth_refresh_time = curr_ms
            
            if time.ticks_diff(curr_ms, last_report_time) >= REPORTING_INTERVAL_MS:
                last_report_time = curr_ms
                # safely read shared state
                with data_lock:
                    current_reading = abs(latest_smoothed_frequency)
                
                print(f"reading: {current_reading:0.2f}, auth ttl: {auth_ttl}")
               
                # don't send values very similar to the last reading
                if not math.isclose(current_reading, last_reading, abs_tol=READING_TOLERANCE):
                    timestamp = get_formatted_time()
                    try: 
                        send_to_firebase(
                            current_reading,
                            timestamp,
                            secrets.FIREBASE_DB_NAME,
                            secrets.FIREBASE_DATA_PATH,
                            gcp_access_token) # type: ignore
                        last_reading = current_reading
                    except Exception as e:
                        print(f"main core: failed to send data: {e}")

            time.sleep_ms(100)
    except Exception as e:
        print(f"error occurred in main loop: {e}")
    finally:
        print("turning off sensor loop")
        sensor_loop_may_proceed = False


if __name__ == "__main__":
    main_loop()