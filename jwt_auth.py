import time
import ujson
import urequests
import ubinascii
# custom micropython fast RSA module
import fastrsa
# credentials
import secrets
from micropython import const

# --- Constants ---
# Google's required algorithm for JWT signing
JWT_ALG = const('RS256')
# JWTs are valid for a maximum of 1 hour (3600 seconds)
JWT_EXP_DELTA_SECONDS = const(3600)

JWT_BODY_FMT = const("grant_type=urn%%3Aietf%%3Aparams%%3Aoauth%%3Agrant-type%%3Ajwt-bearer&assertion=%s")
JWT_REQ_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


AUTH_BEARER_FMT = "Bearer %s"
AUTH_HEADERS = {
    "Content-Type": "application/json",
    "authorization": None
}

JWT_PAYLOAD = {
    "iss": secrets.GCP_CLIENT_EMAIL,
    "sub": secrets.GCP_CLIENT_EMAIL,
    "aud": secrets.GCP_TOKEN_URI,
    "iat": None, #current_unix_time,
    "exp": None, #current_unix_time + JWT_EXP_DELTA_SECONDS,
    "scope": secrets.GCP_SCOPE
}


def _b64url_encode(data):
    """
    Helper function to perform Base64 URL-safe encoding.
    This replaces '+' with '-' and '/' with '_' and removes padding.
    """
    encoded = ubinascii.b2a_base64(data)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').rstrip(b'=\n')


JWT_HEADER = _b64url_encode(ujson.dumps({
    "alg": JWT_ALG,
    "typ": "JWT"
}).encode("utf-8"))


# --- Main Authentication Logic ---
def get_signed_jwt(current_unix_time):
    """
    Creates a signed JWT and exchanges it for a GCP access token.
    
    Returns:
        The access token string if successful, otherwise None.
    """
    JWT_PAYLOAD["iat"] = current_unix_time
    JWT_PAYLOAD["exp"] = current_unix_time + JWT_EXP_DELTA_SECONDS

    # create and sign the JWT
    try:
        # Encode header and payload as JSON, then Base64 URL-safe encode them
        encoded_header = JWT_HEADER
        encoded_payload = _b64url_encode(ujson.dumps(JWT_PAYLOAD).encode('utf-8'))
        
        # Create the signing input string (header.payload)
        signing_input = encoded_header + b'.' + encoded_payload
   
        n_bytes = ubinascii.unhexlify(secrets.RSA_N_HEX)
        e_bytes = ubinascii.unhexlify(secrets.RSA_E_HEX)
        d_bytes = ubinascii.unhexlify(secrets.RSA_D_HEX)
        p_bytes = ubinascii.unhexlify(secrets.RSA_P_HEX)
        q_bytes = ubinascii.unhexlify(secrets.RSA_Q_HEX)
  
        signature = fastrsa.sign(
            signing_input,
            n_bytes,
            e_bytes,
            d_bytes,
            p_bytes,
            q_bytes
        )
        
        # Base64 URL-safe encode the signature
        encoded_signature = _b64url_encode(signature)
         
        # Concatenate to form the final JWT string
        signed_jwt = signing_input.decode('utf-8') + '.' + encoded_signature.decode('utf-8')
        return signed_jwt
    except Exception as e:
        print(f"Error: Failed to sign JWT. Check your private key components. {e}")
        return None


def exchange_jwt_for_access_token(signed_jwt):
    # 4. Exchange the signed JWT for an access token
    response = None
    try:
        # The body must be URL-encoded
        body = JWT_BODY_FMT % signed_jwt
        
        response = urequests.post(
            secrets.GCP_TOKEN_URI,
            headers=JWT_REQ_HEADERS,
            data=body
        )
        
        status_code = response.status_code
        response_json = response.json()

        if status_code == 200:
            access_token = response_json.get("access_token")
            return access_token
        else:
            print("error: failed to get access token.")
            print("response:", ujson.dumps(response_json))
            return None

    except Exception as e:
        print(f"error: An exception occurred during the POST request. {e}")
        return None
    finally:
        if response:
            response.close()


def get_jwt_access_token():
    # current time as a Unix timestamp 
    current_unix_time = time.time()
    jwt = get_signed_jwt(current_unix_time)
    return exchange_jwt_for_access_token(jwt)


def get_jwt_auth_headers():
  access_token = get_jwt_access_token()
  AUTH_HEADERS["authorization"] = AUTH_BEARER_FMT % access_token
  return AUTH_HEADERS
