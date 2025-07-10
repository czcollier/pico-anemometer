# Save this as key_extractor.py on your Linux machine.
# You will need to install the 'pycryptodome' library: pip install pycryptodome
import sys
from Crypto.PublicKey import RSA
import json

# --- CONFIGURATION ---
# Path to your Google Cloud service account JSON file
# The required key size in bytes (256 for a 2048-bit key)
KEY_SIZE_BYTES = 256

def extract_key_components(service_account_file):
    """
    Parses a Google service account key file and extracts the
    modulus (n) and private exponent (d) as hex strings.
    """
    print(f"Loading service account key from: {service_account_file}")
    
    with open(service_account_file, 'r') as f:
        key_data = json.load(f)
    
    private_key_pem = key_data['private_key']
    
    try:
        key = RSA.import_key(private_key_pem)
    except Exception as e:
        print(f"Error importing key: {e}")
        return

    # Extract the components as integers
    n = key.n
    d = key.d

    # Convert them to fixed-length, big-endian byte strings
    n_bytes = n.to_bytes(KEY_SIZE_BYTES, 'big')
    d_bytes = d.to_bytes(KEY_SIZE_BYTES, 'big')

    # Convert to hex for easy storage and printing
    n_hex = n_bytes.hex()
    d_hex = d_bytes.hex()

    print("\n--- Success! ---")
    print("Copy these values into your secrets.py file on the Pico.\n")
    
    print("# Modulus (n)")
    print(f"RSA_N_HEX = '{n_hex}'\n")
    
    print("# Private Exponent (d)")
    print(f"RSA_D_HEX = '{d_hex}'\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("key file command parameter needed")
        sys.exit(1)

    keyfile = sys.argv[1]
    extract_key_components(keyfile)
