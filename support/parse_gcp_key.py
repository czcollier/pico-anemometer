# parse_gcp_key.py
import json
from Crypto.PublicKey import RSA

# --- IMPORTANT ---
# Replace this with the actual path to the JSON key file you downloaded from GCP.
gcp_key_file_path = './pound-weather-firebase-adminsdk-fbsvc-7d78b80d71.json'

print(f"Processing key file: {gcp_key_file_path}")

try:
    with open(gcp_key_file_path, 'r') as f:
        key_data = json.load(f)

    private_key_pem = key_data['private_key']
    
    # Import the PEM key using the powerful pycryptodome library
    key = RSA.import_key(private_key_pem)

    # Extract the raw integer components
    print("\nSuccess! Copy the following lines into your secrets.py file on the Pico:\n")
    print(f"GCP_PK_N = {key.n}")
    print(f"GCP_PK_E = {key.e}")
    print(f"GCP_PK_D = {key.d}")
    print(f"GCP_PK_P = {key.p}")
    print(f"GCP_PK_Q = {key.q}")

except FileNotFoundError:
    print(f"ERROR: The file was not found at '{gcp_key_file_path}'")
except Exception as e:
    print(f"An error occurred: {e}")
