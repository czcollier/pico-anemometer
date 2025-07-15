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
from micropython import const
from timestamp import get_current_timestamp
import pubsub
import firebase

# --- Configuration ---
# sensor
READING_TOLERANCE: float = const(0.05)
SENSOR_DEBUG_MODE: bool = False

SENSOR_PIN: int = const(15)
SAMPLING_INTERVAL: int = const(20)
SMOOTHING_WINDOW_LEN_MS: int = const(8000)
FREQUENCY_COUNTER_TIMEOUT: int = const(5000)
SMOOTHING_WINDOW_SIZE: int = const(
    int(SMOOTHING_WINDOW_LEN_MS / SAMPLING_INTERVAL))

# data upload
REPORTING_INTERVAL_MS: int = const(8000)
WIFI_CONNECT_SLEEP_S: int = const(10)
TIMESTAMP_FORMAT = const("%d-%02d-%02d %02d:%02d:%02d")
USE_PUBSUB = False

# auth
AUTH_TOKEN_EXPIRY_MS: int = const(1000 * 3600)
AUTH_REFRESH_INTERVAL_MS: int = const(int(AUTH_TOKEN_EXPIRY_MS * 0.9))
NTP_RETRIES: int = const(20)
NTP_FAILURE_LENIENT: bool = False
JWT_RETRIES = const(20)
CLOCK_USES_LOCAL_TIME = True

# Global data shared between cores
sensor_loop_may_proceed: bool = True
latest_smoothed_frequency: float = 0.0
# lock for latest_smoothed_frequency
data_lock = _thread.allocate_lock()


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


def google_jwt_authenticate(ntp_failure_lenient: bool=False):
    time_synced = ntp.sync_clock_to_ntp(NTP_RETRIES)

    if not time_synced:
        print("error: Could not sync time with NTP after multiple attempts.")
        if not ntp_failure_lenient:
            print("Cannot proceed without accurate time.")
            return None
        else:
            print("continuing without syncing time to ntp and hoping for the best")
    jwt_auth_headers: dict | None = None
    jwt_try = 1
    while jwt_auth_headers is None and jwt_try <= JWT_RETRIES:
        print("attempting to get JWT access token")
        jwt_try += 1
        jwt_auth_headers = jwt_auth.get_jwt_auth_headers()

    return jwt_auth_headers


def main_loop() -> None:
    global sensor_loop_may_proceed
    try:
        # --- Start the sensor loop on the second core ---
        _thread.start_new_thread(sensor_loop, ())

        # --- Connect to Wi-Fi on the main core ---
        connect_to_wifi()

        jwt_auth_headers = google_jwt_authenticate(NTP_FAILURE_LENIENT)

        start_ms = time.ticks_ms()
        last_auth_refresh_time = start_ms
        last_report_time = start_ms - REPORTING_INTERVAL_MS
        last_reading = 0
        led = machine.Pin("LED", machine.Pin.OUT)
        print("main core: startng main network loop")

        # --- main loop for main core ---
        while True:
            curr_ms = time.ticks_ms()
            
            if time.ticks_diff(curr_ms, last_report_time) >= REPORTING_INTERVAL_MS:
                # CONNECTION WATCHDOG: Check if we are still connected.
                if not czc_wifi.is_wifi_connected():
                    print("main core: Wi-Fi connection lost. Attempting to reconnect...")
                    connect_to_wifi() 
                    time.sleep(WIFI_CONNECT_SLEEP_S)
                    continue # skip the rest of this loop iteration

                auth_ttl = int((AUTH_REFRESH_INTERVAL_MS
                    - time.ticks_diff(curr_ms, last_auth_refresh_time)) / 1000)

                if  auth_ttl <= 0:
                    jwt_auth_headers = google_jwt_authenticate(NTP_FAILURE_LENIENT)
                    last_auth_refresh_time = curr_ms
                
                last_report_time = curr_ms
                # safely read shared state
                with data_lock:
                    current_reading = round(abs(latest_smoothed_frequency), 2)
            
                print("reading: ", current_reading, " auth ttl: ", auth_ttl)
               
                # don't send values very similar to the last reading
                if not math.isclose(current_reading, last_reading, abs_tol=READING_TOLERANCE):
                    timestamp = get_current_timestamp() 
                    try:
                        led.on() 
                        firebase.send_to_firebase(
                            current_reading,
                            timestamp,
                            jwt_auth_headers) # type: ignore
                        if USE_PUBSUB:
                            pubsub.publish(
                                current_reading,
                                timestamp,
                                jwt_auth_headers)
                        led.off()
                        last_reading = current_reading
                    except Exception as e:
                        print("main core: failed to send data: ", e)

            time.sleep_ms(100)

    except Exception as e:
        print("error occurred in main loop: ", e)
    finally:
        print("turning off sensor loop")
        sensor_loop_may_proceed = False


if __name__ == "__main__":
    main_loop()
