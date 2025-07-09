import network
import time

NETWORK_CONNECT_WAIT_SEC = 300
wifi = None

def is_wifi_connected():
    global wifi
    return wifi is not None and wifi.isconnected()


def connect_wifi(ssid, password):
    global wifi
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
            time.sleep(1)

    print("WiFi Connected!")
    print("IP Info:", wifi.ifconfig())
    return True