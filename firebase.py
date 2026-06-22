import urequests
import secrets
from micropython import const

import jwt_auth
import ntp

NTP_RETRIES: int = const(20)
NTP_FAILURE_LENIENT: bool = False
JWT_RETRIES = const(20)

FB_DB_NAME = secrets.FIREBASE_DB_NAME
FB_DATA_PATH = secrets.FIREBASE_DATA_PATH

FB_URL_FMT: str = const("https://%s.firebaseio.com/%s")
FB_MESSAGE = {
    "wind_speed": 0.0,
    "timestamp": "",
    "source": "device_" + secrets.SENSOR_ID,
}


def google_jwt_authenticate(
        ntp_retries: int=NTP_RETRIES,
        ntp_failure_lenient: bool=False,
        jwt_retries: int=JWT_RETRIES) -> dict | None:
    time_synced = ntp.sync_clock_to_ntp(ntp_retries)

    if not time_synced:
        print("error: Could not sync time with NTP after multiple attempts.")
        if not ntp_failure_lenient:
            print("Cannot proceed without accurate time.")
            return None
        else:
            print("continuing without syncing time to ntp and hoping for the best")
    jwt_auth_headers: dict | None = None
    jwt_try = 1
    while jwt_auth_headers is None and jwt_try <= jwt_retries:
        print("attempting to get JWT access token")
        jwt_try += 1
        jwt_auth_headers = jwt_auth.get_jwt_auth_headers()

    return jwt_auth_headers


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


def get_from_firebase(auth_headers: dict | None) -> dict | None:
    if auth_headers == None:
        return None

    response = None
    try:
        fbase_url = FB_URL_FMT % (FB_DB_NAME, FB_DATA_PATH)
        response = urequests.get(
            url=fbase_url,
            headers=auth_headers)
        
        return response.json()
    except Exception as e:
        print("error fetching from Firebase: ", e)
    finally:
        if response:
            response.close()