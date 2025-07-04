from utime import sleep

class FrequencyCounter:
  def __init__(self, high_threshold, low_threshold, timeout_ms):
    self._high_threshold = high_threshold
    self._low_threshold = low_threshold
    self._timeout_ms = timeout_ms

    self._is_armed = False
    self._has_started = False
    self._current_frequency = 0.0
    self._last_event_time = 0
  
  def update(self, current_ms, sensor_value):
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


  def get_frequency(self):
    return self._current_frequency

  