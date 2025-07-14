import network
import time
from micropython import const
import machine

NETWORK_CONNECT_WAIT_SEC = const(300)

wifi = None

def is_wifi_connected():
    global wifi
    return wifi is not None and wifi.isconnected()


def connect_wifi(ssid, password):
    global wifi

    led = machine.Pin("LED", machine.Pin.OUT)
    """Connects the device to a Wi-Fi network."""
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    
    while not wifi.isconnected():
        print(f"Connecting to Wi-Fi network: {ssid}...")
        wifi.connect(ssid, password)
        # Wait for connection with a timeout
        max_wait = NETWORK_CONNECT_WAIT_SEC
        while max_wait > 0:
            if wifi.status() < 0 or wifi.status() >= 3:
                break
            max_wait -= 1
            print('.')
            #led.on()
            time.sleep(1)
            #led.off()
    print("WiFi Connected!")
    print("IP Info:", wifi.ifconfig())
    return True