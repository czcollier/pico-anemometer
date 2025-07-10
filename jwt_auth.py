import time
import ujson
import urequests
import ubinascii
# custom micropython fast RSA module
import fastrsa
# credentials
import secrets

# --- Constants ---
# Google's required algorithm for JWT signing
JWT_ALG = 'RS256'
# JWTs are valid for a maximum of 1 hour (3600 seconds)
JWT_EXP_DELTA_SECONDS = 3600


# --- Helper Function ---
def _b64url_encode(data):
    """
    Helper function to perform Base64 URL-safe encoding.
    This replaces '+' with '-' and '/' with '_' and removes padding.
    """
    encoded = ubinascii.b2a_base64(data)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').rstrip(b'=\n')


# --- Main Authentication Logic ---
def get_jwt_access_token():
    """
    Creates a signed JWT and exchanges it for a GCP access token.
    
    Returns:
        The access token string if successful, otherwise None.
    """
    print("\n--- Starting GCP Authentication ---")

    # 2. Define the JWT Header and Payload (Claims)
    header = {
        "alg": JWT_ALG,
        "typ": "JWT"
    }

    # current time as a Unix timestamp 
    current_unix_time = time.time()
    
    payload = {
        "iss": secrets.GCP_CLIENT_EMAIL,
        "sub": secrets.GCP_CLIENT_EMAIL,
        "aud": secrets.GCP_TOKEN_URI,
        "iat": current_unix_time,
        "exp": current_unix_time + JWT_EXP_DELTA_SECONDS,
        "scope": secrets.GCP_SCOPE
    }

    # create and sign the JWT
    try:
        print("creating JWT...")

        print("encoding header and payload...") 
        # Encode header and payload as JSON, then Base64 URL-safe encode them
        encoded_header = _b64url_encode(ujson.dumps(header).encode('utf-8'))
        encoded_payload = _b64url_encode(ujson.dumps(payload).encode('utf-8'))
        
        print("building signing input...") 
        # Create the signing input string (header.payload)
        signing_input = encoded_header + b'.' + encoded_payload
   
        print("preparing key bytes...")        
        n_bytes = ubinascii.unhexlify(secrets.RSA_N_HEX)
        e_bytes = ubinascii.unhexlify(secrets.RSA_E_HEX)
        d_bytes = ubinascii.unhexlify(secrets.RSA_D_HEX)
        p_bytes = ubinascii.unhexlify(secrets.RSA_P_HEX)
        q_bytes = ubinascii.unhexlify(secrets.RSA_Q_HEX)
  
        print("signing...") 
        signature = fastrsa.sign(
            signing_input,
            n_bytes,
            e_bytes,
            d_bytes,
            p_bytes,
            q_bytes
        )
        
        #print("Signing JWT with RS256...")
        #signature = rsa.sign(signing_input, private_key, 'SHA-256')
        
        print("encoding signature...") 
        # Base64 URL-safe encode the signature
        encoded_signature = _b64url_encode(signature)
         
        print("creating signed jwt...") 
        # Concatenate to form the final JWT string
        signed_jwt = signing_input.decode('utf-8') + '.' + encoded_signature.decode('utf-8')
        print("JWT created and signed successfully.")
        
    except Exception as e:
        print(f"Error: Failed to sign JWT. Check your private key components. {e}")
        return None

    # 4. Exchange the signed JWT for an access token
    try:
        print("requesting access token")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # The body must be URL-encoded
        body = f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion={signed_jwt}"
        
        response = urequests.post(
            secrets.GCP_TOKEN_URI,
            headers=headers,
            data=body
        )
        
        status_code = response.status_code
        response_json = response.json()
        response.close()

        #print(f"Received response with status code: {status_code}")
        
        if status_code == 200:
            access_token = response_json.get("access_token")
            print("successfully obtained access token!")
            return access_token
        else:
            print("error: failed to get access token.")
            print("response:", ujson.dumps(response_json))
            return None
            
    except Exception as e:
        print(f"error: An exception occurred during the POST request. {e}")
        return None
