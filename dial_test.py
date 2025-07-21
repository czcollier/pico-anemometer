import machine
import time

# --- Configuration ---
# The GPIO pin your dial is connected to.
DIAL_PIN = 12 

# The frequency of the PWM signal in Hz. 1000 Hz is a good starting point.
# A higher frequency gives a smoother output but consumes slightly more power.
PWM_FREQUENCY = 1000

# The number of steps to use for the sweep (e.g., 100 steps).
# More steps = finer control, but a longer test.
CALIBRATION_STEPS = 100
MAX_DUTY_CYCLE = 23500
MAX_WS = 100
# How long to pause at each step (in seconds) so you can read the dial.
PAUSE_PER_STEP_S = 2

# --- Setup ---
try:
    # Set up the PWM pin
    pwm_pin = machine.Pin(DIAL_PIN)
    pwm_out = machine.PWM(pwm_pin)
    pwm_out.freq(PWM_FREQUENCY)
    
    print("--- Starting Dial Calibration Sweep ---")
    print(f"Pin: GP{DIAL_PIN}, Frequency: {PWM_FREQUENCY} Hz")
    print("The script will now slowly increase the voltage.")
    print("At each step, note the duty cycle value and the wind speed on the dial.\n")
    calibration_step_sz = int(MAX_WS / CALIBRATION_STEPS) 

    # --- Calibration Loop ---
    for i in range(CALIBRATION_STEPS + 1):
        # Calculate the duty cycle value for the current step
        # The duty cycle is a 16-bit value from 0 to 65535
        mock_ws = i * calibration_step_sz
        duty_cycle_value = int((mock_ws / MAX_WS) * MAX_DUTY_CYCLE)
        
        # Apply the duty cycle to the PWM pin
        pwm_out.duty_u16(duty_cycle_value)
        
        # Print the current value for your notes
        print(f"Step {i}/{CALIBRATION_STEPS} -> Wind Speed: {mock_ws} Duty Cycle: {duty_cycle_value}")
        
        # Pause to allow you to read the physical dial
        time.sleep(PAUSE_PER_STEP_S)

    # --- Cleanup ---
    print("\n--- Calibration Sweep Complete ---")

except Exception as e:
    print(f"An error occurred: {e}")
    print("Please check that you have the correct DIAL_PIN configured.")
finally:
    # Turn off the PWM output
    pwm_out.duty_u16(0)
    pwm_out.deinit()
    print("PWM pin has been turned off.")
