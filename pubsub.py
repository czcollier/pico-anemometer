import jwt_auth
import urequests
import ujson
import ubinascii
from timestamp import get_current_timestamp

PUBSUB_URL = "https://pubsub.googleapis.com/v1/projects/pound-weather/topics/sensors:publish"

MESSAGE: dict = {
    "messages": [{
    "data": None,
    "ordering_key": "timestamp"
}]}


def publish(wind_speed: float, timestamp: str, auth_headers):
    response = None
    try:
        payload = ujson.dumps({
            "wind_speed": wind_speed,
            "timestamp": timestamp
        })

        encoded_data = (ubinascii.b2a_base64(payload.encode('utf-8'))
                        .decode('utf-8').strip())

        MESSAGE["data"] = encoded_data
        
        response = urequests.post(PUBSUB_URL, headers=auth_headers, data=ujson.dumps(MESSAGE))
        return response 
    except Exception as e:
        print("ERROR occurred sending to pubsub: ", e)
    finally:
        if response:
            response.close()