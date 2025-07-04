import time
import ujson
import urequests
import ntptime
import ubinascii
# Custom libraries placed in /lib
# The microjwt library is no longer needed.
import rsa

# Your credentials stored in a separate file
import secrets

# --- Constants ---
# Google's required algorithm for JWT signing
JWT_ALG = 'RS256'
# JWTs are valid for a maximum of 1 hour (3600 seconds)
JWT_EXP_DELTA_SECONDS = 3600


# --- Helper Function ---
def b64url_encode(data):
    """
    Helper function to perform Base64 URL-safe encoding.
    This replaces '+' with '-' and '/' with '_' and removes padding.
    """
    encoded = ubinascii.b2a_base64(data)
    return encoded.replace(b'+', b'-').replace(b'/', b'_').rstrip(b'=\n')


# --- Main Authentication Logic ---
def get_gcp_access_token():
    """
    Creates a signed JWT and exchanges it for a GCP access token.
    
    Returns:
        The access token string if successful, otherwise None.
    """
    print("\n--- Starting GCP Authentication ---")
    
    # 1. Sync time with NTP server. This is CRITICAL for JWT 'iat' and 'exp' claims.
    time_synced = False
    for i in range(5): # Try up to 5 times
        try:
            print(f"syncing time with NTP server (Attempt {i+1}/5)...")
            ntptime.settime()
            time_synced = True
            # **DEBUGGING STEP**: Print the time after sync to verify it's correct (in UTC).
            synced_time = time.localtime()
            print(f"time synced successfully. Current UTC time: {synced_time[0]}-{synced_time[1]:02d}-{synced_time[2]:02d} {synced_time[3]:02d}:{synced_time[4]:02d}:{synced_time[5]:02d}")
            break # Exit the loop on success
        except Exception as e:
            print(f"warning: NTP sync attempt failed. {e}")
            time.sleep(2) # Wait 2 seconds before retrying

    if not time_synced:
        print("error: Could not sync time with NTP after multiple attempts.")
        print("Cannot proceed without accurate time.")
        return None

    # 2. Define the JWT Header and Payload (Claims)
    header = {
        "alg": JWT_ALG,
        "typ": "JWT"
    }

    # Get current time as a Unix timestamp (seconds since 1970)
    current_unix_time = time.time()
    
    payload = {
        "iss": secrets.GCP_CLIENT_EMAIL,
        "sub": secrets.GCP_CLIENT_EMAIL,
        "aud": secrets.GCP_TOKEN_URI,
        "iat": current_unix_time,
        "exp": current_unix_time + JWT_EXP_DELTA_SECONDS,
        "scope": secrets.GCP_SCOPE
    }
    
    #print("\nJWT Payload (Claims):")
    #print(ujson.dumps(payload))

    # 3. Manually create and sign the JWT
    try:
        print("creating JWT...")
        
        # Encode header and payload as JSON, then Base64 URL-safe encode them
        encoded_header = b64url_encode(ujson.dumps(header).encode('utf-8'))
        encoded_payload = b64url_encode(ujson.dumps(payload).encode('utf-8'))
        
        # Create the signing input string (header.payload)
        signing_input = encoded_header + b'.' + encoded_payload
        
        #print("Loading private key from components...")
        private_key = rsa.PrivateKey(
            secrets.GCP_PK_N,
            secrets.GCP_PK_E,
            secrets.GCP_PK_D,
            secrets.GCP_PK_P,
            secrets.GCP_PK_Q
        )
        
        #print("Signing JWT with RS256...")
        signature = rsa.sign(signing_input, private_key, 'SHA-256')
        
        # Base64 URL-safe encode the signature
        encoded_signature = b64url_encode(signature)
        
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
