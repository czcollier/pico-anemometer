# Save this as key_extractor.py on your Linux machine.
# You will need to install 'pycryptodome': pip install pycryptodome
import sys
from Crypto.PublicKey import RSA
import json

# --- CONFIGURATION ---
SERVICE_ACCOUNT_FILE = 'path/to/your/service-account.json'

def extract_key_components(service_account_file):
    """
    Parses a Google service account key file and extracts all RSA
    private key components as hex strings for use with mbedtls.
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

    # Extract all components as integers
    n, e, d, p, q = key.n, key.e, key.d, key.p, key.q

    # Convert them to fixed-length, big-endian byte strings
    key_size_bytes = (key.n.bit_length() + 7) // 8
    p_q_size_bytes = (key.p.bit_length() + 7) // 8

    n_bytes = n.to_bytes(key_size_bytes, 'big')
    e_bytes = e.to_bytes(3, 'big') # 'e' is usually 65537, which fits in 3 bytes
    d_bytes = d.to_bytes(key_size_bytes, 'big')
    p_bytes = p.to_bytes(p_q_size_bytes, 'big')
    q_bytes = q.to_bytes(p_q_size_bytes, 'big')

    print("\n--- Success! ---")
    print("Copy these variables into your secrets.py file on the Pico.\n")
    
    print(f"RSA_N_HEX = '{n_bytes.hex()}'")
    print(f"RSA_E_HEX = '{e_bytes.hex()}'")
    print(f"RSA_D_HEX = '{d_bytes.hex()}'")
    print(f"RSA_P_HEX = '{p_bytes.hex()}'")
    print(f"RSA_Q_HEX = '{q_bytes.hex()}'")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("key file command parameter needed")
        sys.exit(1)

    keyfile = sys.argv[1]
    extract_key_components(keyfile)