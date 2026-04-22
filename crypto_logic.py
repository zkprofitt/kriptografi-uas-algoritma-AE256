from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

# Pastikan kuncinya tetap sama
KEY = b'ini_kunci_rahasia_32_byte_fix_ok' 

# Update fungsi ini supaya bisa nerima IV tambahan (posisi argumen ke-2)
def encrypt_data(plaintext, common_iv=None):
    # Jika common_iv dikirim dari app.py, pakai itu. Kalau nggak, buat baru.
    cipher = AES.new(KEY, AES.MODE_CBC, iv=common_iv) if common_iv else AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return cipher.iv, base64.b64encode(ct_bytes).decode('utf-8')

def decrypt_data(iv_base64, ct_base64):
    try:
        iv = base64.b64decode(iv_base64)
        ct = base64.b64decode(ct_base64)
        cipher = AES.new(KEY, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')
    except:
        return "Gagal Dekripsi"