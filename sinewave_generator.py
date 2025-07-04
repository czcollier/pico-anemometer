import math

class SinewaveGenerator:
  """
  Generates a sine wave point by point.
  """

  def __init__(self, amplitude: float, offset: float, sampling_rate: int):
    """
    Initializes the SinewaveGenerator.

    Args:
      amplitude: The peak deviation of the wave from the offset. 
                 The wave will run from (offset - amplitude) to (offset + amplitude).
      offset: The value around which the sine wave is centered.
      sampling_rate: The number of samples per second.
    """
    self._amplitude = amplitude
    self._offset = offset
    self._sampling_rate = sampling_rate
    self._current_angle = 0.0

  def generate_sine_wave_point(self, frequency: float) -> float:
    """
    Generates the next point on a sine wave based on a fixed sampling rate.

    This method uses an instance variable to maintain the current angle,
    incrementing it on each call to produce a continuous wave. It should be
    called at a regular interval, corresponding to the sampling_rate.

    Args:
      frequency: The desired frequency of the sine wave in Hertz (Hz).

    Returns:
      The next floating-point value in the sine wave sequence.
    """
    # Calculate the value for the current angle
    output_value = self._offset + self._amplitude * math.sin(self._current_angle)

    # Increment the angle for the next call
    # The change in angle per sample is determined by the wave frequency
    # and how often we sample it.
    # Angular frequency (rad/s) = 2 * PI * frequency
    # Angle increment = Angular frequency / Sampling rate
    # Note: The original C++ code had a division by 10 in the angle increment
    # calculation (samplingRate / 10.0), which is unusual. This has been
    # preserved in this translation. If this was a mistake in the original
    # code, you may want to remove the '/ 10.0'.
    angle_increment = (2.0 * math.pi * frequency) / (self._sampling_rate / 10.0)

    self._current_angle += angle_increment

    # Keep the angle from growing infinitely large by wrapping it at 2*PI (a full circle).
    # The modulo operator (%) in Python works for floating-point numbers.
    self._current_angle %= (2.0 * math.pi)

    return output_value

  def reset_angle(self):
    """
    Resets the maintained angle to zero.
    """
    self._current_angle = 0.0