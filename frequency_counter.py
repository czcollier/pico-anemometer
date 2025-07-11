import micropython

class FrequencyCounter:
  def __init__(
      self,
      high_threshold: float,
      low_threshold: float,
      timeout_ms: int):
    self._high_threshold: float = high_threshold
    self._low_threshold: float = low_threshold
    self._timeout_ms: int = timeout_ms

    self._is_armed: bool = False
    self._has_started: bool = False
    self._current_frequency: float = 0.0
    self._last_event_time: int = 0
  
  @micropython.native
  def update(self, current_ms: int, sensor_value: int) -> None:
    if sensor_value < self._low_threshold:
      self._is_armed = True

    if self._is_armed and sensor_value > self._high_threshold:
      if self._has_started:
        period = current_ms - self._last_event_time
        if period == 0.0:
          self._current_frequency = 0.0
        else:
          self._current_frequency = 1000.0 / period

      self._last_event_time = current_ms
      self._is_armed = False
      self._has_started = True

    if self._has_started and (current_ms - self._last_event_time > self._timeout_ms):
      self._current_frequency = 0.0
      self._has_started = False

  @micropython.native
  def get_frequency(self) -> float:
    return self._current_frequency

  