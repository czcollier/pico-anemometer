# --- Constants ---
STA_IF = 1 # Station interface

class WLAN:
    """
    This is a mock WLAN class for running on a local Linux machine.
    It allows the main code to run without modification.
    """
    def __init__(self, interface_id):
        self._active = False
        self._connected = False
        print(f"MockWLAN: Initialized for interface {interface_id}")

    def active(self, is_active=None):
        if is_active is None:
            return self._active
        self._active = bool(is_active)
        print(f"MockWLAN: Set active to {self._active}")

    def isconnected(self):
        # On Linux, we assume we are always connected to the internet.
        return True

    def connect(self, ssid, password):
        print(f"MockWLAN: Pretending to connect to SSID '{ssid}'...")
        self._connected = True
        print("MockWLAN: Connection successful (mocked).")

    def ifconfig(self):
        # Return some dummy data that looks like the real thing.
        return ('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8')
