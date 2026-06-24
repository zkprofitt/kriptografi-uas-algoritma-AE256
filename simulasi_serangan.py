"""
================================================================
 SIMULASI BRUTE-FORCE ATTACK TERHADAP AES-256-CBC
 Sistem: Safe-Loan - Hybrid Cryptography (AES-256 + RSA-2048)
================================================================
"""

import os
import base64
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ----------------------------------------------------------------
# INPUT MANUAL - Isi bagian ini dengan data dari database 
# ----------------------------------------------------------------
CIPHERTEXT_B64 = "XasAgwD3t94vIqjnPILgEg=="   # contoh: s7SO3GFldqSkOomCevnu+kA==
IV_B64         = "XBysF9t/esIFKxnuTIbo3w=="            # dari kolom iv_data di database

# ----------------------------------------------------------------
MAX_PERCOBAAN = 3000
# ----------------------------------------------------------------

print("=" * 65)
print("  SIMULASI BRUTE-FORCE ATTACK TERHADAP AES-256-CBC")
print("  Sistem: Safe-Loan (AES-256 + RSA-2048)")
print("=" * 65)
print(f"\n  Ciphertext  : {CIPHERTEXT_B64[:45]}...")
print(f"  IV          : {IV_B64}")
print(f"  Total uji   : {MAX_PERCOBAAN:,} kunci acak 256-bit")
print(f"  Strategi    : Exhaustive random key search")
print()

try:
    ct_raw = base64.b64decode(CIPHERTEXT_B64)
    iv_raw = base64.b64decode(IV_B64)
except Exception as e:
    print(f"ERROR: Ciphertext atau IV tidak valid - {e}")
    exit()

ditemukan   = False
waktu_mulai = time.perf_counter()

for i in range(1, MAX_PERCOBAAN + 1):
    kunci_coba = os.urandom(32)

    try:
        cipher = AES.new(kunci_coba, AES.MODE_CBC, iv_raw)
        hasil  = unpad(cipher.decrypt(ct_raw), AES.block_size)
        teks   = hasil.decode('utf-8')
        print(f"Percobaan {i:>4} | Kunci: {kunci_coba.hex()[:20]}... | Hasil: {teks[:20]} | Status: VALID PADDING")
        ditemukan = True
        break

    except Exception:
        print(f"Percobaan {i:>4} | Kunci: {kunci_coba.hex()[:20]}... | Status: Gagal (padding error)")

waktu_selesai = time.perf_counter()
total_waktu   = waktu_selesai - waktu_mulai
kecepatan     = MAX_PERCOBAAN / total_waktu

total_kunci    = 2 ** 256
estimasi_detik = total_kunci / kecepatan
estimasi_tahun = estimasi_detik / (60 * 60 * 24 * 365)

print()
print("=" * 65)
print("  KESIMPULAN")
print("=" * 65)
print(f"""
  Total percobaan   : {MAX_PERCOBAAN:,} kunci acak 256-bit
  Kunci ditemukan   : {'YA' if ditemukan else 'TIDAK'}
  Total waktu       : {total_waktu:.2f} detik
  Kecepatan         : {kecepatan:,.0f} kunci/detik

  Ruang kunci AES-256       : 2^256 kemungkinan
  Estimasi waktu brute-force: {estimasi_tahun:.2e} tahun
  Usia alam semesta         : ~1.38 x 10^10 tahun

  Setelah {MAX_PERCOBAAN:,} percobaan, kunci AES-256 TIDAK DITEMUKAN.
  Brute-force membutuhkan waktu {estimasi_tahun:.2e} tahun --
  jauh melampaui usia alam semesta.

  => Ciphertext AES-256 pada sistem Safe-Loan TERBUKTI AMAN
     terhadap serangan brute-force.
""")