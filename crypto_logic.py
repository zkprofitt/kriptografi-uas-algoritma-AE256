import os
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

# ================================================================
#  SAFE-LOAN: Crypto Logic
#  Algoritma: AES-256-CBC + RSA-2048
#
#  Alur Enkripsi:
#  1. Generate AES key acak (32 byte) per field
#  2. Enkripsi data nasabah dengan AES-256-CBC
#  3. Enkripsi AES key menggunakan RSA public key (Key Wrapping)
#
#  Alur Dekripsi:
#  1. Dekripsi AES key menggunakan RSA private key
#  2. Dekripsi data nasabah menggunakan AES key yang sudah didekripsi
# ================================================================

def load_public_key():
    with open("public_key.pem", "rb") as f:
        return RSA.import_key(f.read())

def load_private_key():
    with open("private_key.pem", "rb") as f:
        return RSA.import_key(f.read())


# ================================================================
#  ENKRIPSI
#  Input  : plaintext (str), common_iv (bytes, opsional)
#  Output : (iv_b64, ciphertext_b64, encrypted_aes_key_b64)
# ================================================================
def encrypt_data(plaintext, common_iv=None):
    # 1. Generate AES key acak 256-bit (32 byte)
    aes_key = os.urandom(32)
    print(f"DEBUG - AES Key (base64) : {base64.b64encode(aes_key).decode()}")
    # 2. Enkripsi data dengan AES-256-CBC
    iv = common_iv if common_iv else os.urandom(16)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    ct_bytes = cipher_aes.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    ct_b64 = base64.b64encode(ct_bytes).decode('utf-8')

    # 3. Enkripsi AES key dengan RSA public key (Key Wrapping)
    public_key = load_public_key()
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    encrypted_aes_key_b64 = base64.b64encode(encrypted_aes_key).decode('utf-8')

    iv_b64 = base64.b64encode(iv).decode('utf-8')

    return iv_b64, ct_b64, encrypted_aes_key_b64


# ================================================================
#  DEKRIPSI
#  Input  : iv_b64, ct_b64, encrypted_aes_key_b64
#  Output : plaintext (str) atau pesan error
# ================================================================
def decrypt_data(iv_b64, ct_b64, encrypted_aes_key_b64):
    try:
        iv                = base64.b64decode(iv_b64)
        ct                = base64.b64decode(ct_b64)
        encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)

        # 1. Dekripsi AES key menggunakan RSA private key
        private_key = load_private_key()
        cipher_rsa  = PKCS1_OAEP.new(private_key)
        aes_key     = cipher_rsa.decrypt(encrypted_aes_key)

        # 2. Dekripsi data dengan AES-256-CBC
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
        pt = unpad(cipher_aes.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')

    except Exception as e:
        return f"Gagal Dekripsi: {e}"