import czc_wifi
import firebase
import secrets
import time
from micropython import const
import machine
import math

OUTPUT_PIN: int = const(12)
PWM_FREQUENCY: int = const(1000)

REPORTING_INTERVAL_MS: int = const(5000)
READING_TOLERANCE: float = const(0.05)
SCALE_FACTOR: float = const(2.5)
MAX_WS: int = const(100)
# hardware maxk is 655535. Dial maxes out at around 24000
MAX_DUTY_CYCLE: int = const(23500)

# auth
AUTH_TOKEN_EXPIRY_MS: int = const(1000 * 3600)
AUTH_REFRESH_INTERVAL_MS: int = const(int(AUTH_TOKEN_EXPIRY_MS * 0.9))
WIFI_CONNECT_SLEEP_S: int = const(10)


def connect_to_wifi() -> None:
    czc_wifi.connect_wifi(secrets.WIFI_SSID, secrets.WIFI_PASS)


def main_loop() -> None:
    try:
        # --- Connect to Wi-Fi on the main core ---
        connect_to_wifi()

        jwt_auth_headers = firebase.google_jwt_authenticate(ntp_failure_lenient=False)
        #jwt_auth_headers = None
        start_ms = time.ticks_ms()
        last_auth_refresh_time = start_ms
        last_report_time = start_ms - REPORTING_INTERVAL_MS
        last_reading = 0
        led = machine.Pin("LED", machine.Pin.OUT)
        print("main core: startng main network loop")
        # Set up the PWM pin
        pwm_pin = machine.Pin(OUTPUT_PIN)
        pwm_out = machine.PWM(pwm_pin)
        pwm_out.freq(PWM_FREQUENCY)
        from sinewave_generator import SinewaveGenerator
        swg = SinewaveGenerator(30, 30, 100)
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
                    jwt_auth_headers = firebase.google_jwt_authenticate(
                        ntp_failure_lenient=False)
                    last_auth_refresh_time = curr_ms
                    if jwt_auth_headers == None:
                        break

                
                fb_response = firebase.get_from_firebase(jwt_auth_headers)
                if fb_response is None:
                    raise Exception("no response from firebase")

                response_data = fb_response.get("wind_speed")
                if response_data is None or not isinstance(response_data, float):
                    raise Exception("response value: ", response_data, " is not a float")

                current_reading = response_data * 2.5
                print("reading: ", current_reading, " auth ttl: ", auth_ttl)
               
                # don't send values very similar to the last reading
                if not math.isclose(current_reading, last_reading, abs_tol=READING_TOLERANCE):
                    # Calculate the duty cycle value for the current step
                    # The duty cycle is a 16-bit value from 0 to 65535
                    duty_cycle_value = int((current_reading / MAX_WS) * MAX_DUTY_CYCLE)
                    
                    print("setting duty cycle: ", duty_cycle_value)

                    # Apply the duty cycle to the PWM pin
                    pwm_out.duty_u16(duty_cycle_value)
        
                last_report_time = curr_ms

            time.sleep_ms(100)
    except Exception as e:
        print("error occurred in main loop: ", e)
    finally:
        # Turn off the PWM output
        pwm_out.duty_u16(0)
        pwm_out.deinit()
        print("exiting. PWM pin has been turned off.")


if __name__ == "__main__":
    main_loop()
