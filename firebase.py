import urequests
import secrets
from micropython import const

FB_DB_NAME = secrets.FIREBASE_DB_NAME
FB_DATA_PATH = secrets.FIREBASE_DATA_PATH

FB_URL_FMT: str = const("https://%s.firebaseio.com/%s")
FB_MESSAGE = {
    "wind_speed": 0.0,
    "timestamp": ""
}

def send_to_firebase(
        frequency_hz: float,
        timestamp: str,
        auth_headers: dict) -> None:
    response = None
    try:
        freq_rounded = round(frequency_hz, 2)
        FB_MESSAGE["wind_speed"] = freq_rounded
        FB_MESSAGE["timestamp"] = timestamp

        fbase_url = FB_URL_FMT % (FB_DB_NAME, FB_DATA_PATH)
        response = urequests.patch(
            url=fbase_url,
            headers=auth_headers,
            json=FB_MESSAGE)
    except Exception as e:
        print("error sending to Firebase: ", e)
    finally:
        if response:
            response.close()
# Ja\oVK:<4F2I>Lv(
# \FHuOLDI%V&F0&N_
# TVQkE3S.V(N,AAp7