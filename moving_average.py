import time

class MovingAverage:
  """
  Calculates a simple moving average over a fixed-size window of values.
  This is useful for smoothing out noisy data.
  """
  def __init__(self, window_size: int):
    """
    Initializes the SlidingWindowAverage.

    Args:
      window_size: The number of data points to include in the average.
    """
    if window_size <= 0:
      raise ValueError("Window size must be a positive integer.")
    self._size = window_size
    # In Python, a list is a much better fit than a raw array.
    self._readings = [0.0] * self._size
    self.clear()

  def clear(self):
    """Clears the history and resets the average."""
    self._current_index = 0
    self._current_sum = 0.0
    self._window_is_full = False
    # Re-initialize the list with zeros
    for i in range(self._size):
      self._readings[i] = 0.0

  def add_value(self, new_value: float):
    """
    Adds a new value to the window, replacing the oldest value if the
    window is full.

    Args:
      new_value: The new data point to add.
    """
    # Subtract the oldest value (the one we are about to replace)
    self._current_sum -= self._readings[self._current_index]
    
    # Add the new value to the readings list and the sum
    self._readings[self._current_index] = new_value
    self._current_sum += new_value

    # Move to the next index
    self._current_index += 1
    
    # Handle wrapping the index and check if the window has become full
    if self._current_index >= self._size:
      self._current_index = 0
      self._window_is_full = True

  def get_average(self) -> float:
    """
    Gets the current average of the values in the window.

    Returns:
      The calculated average. Returns 0.0 if no values have been added.
    """
    if self._window_is_full:
      # If the window is full, the average is the sum over the full size
      return self._current_sum / self._size
    else:
      # Before the window is full, the average is over the number of items
      # that have actually been added.
      if self._current_index == 0:
        return 0.0
      return self._current_sum / self._current_index
