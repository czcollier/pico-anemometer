import network
import time

NETWORK_CONNECT_WAIT_SEC = 15

def connect_wifi(ssid, password):
    """Connects the device to a Wi-Fi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    while not wlan.isconnected():
        print(f"Connecting to Wi-Fi network: {ssid}...")
        wlan.connect(ssid, password)
        # Wait for connection with a timeout
        max_wait = NETWORK_CONNECT_WAIT_SEC
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('.')
            time.sleep(1)

    print("WiFi Connected!")
    print("IP Info:", wlan.ifconfig())
    return True