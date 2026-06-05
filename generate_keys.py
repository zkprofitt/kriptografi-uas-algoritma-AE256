from Crypto.PublicKey import RSA

def generate_rsa_keys():
    print("🔑 Generating RSA-2048 key pair...")
    key = RSA.generate(2048)

    # Simpan private key
    with open("private_key.pem", "wb") as f:
        f.write(key.export_key())
    print("✅ private_key.pem berhasil dibuat (JANGAN disebarkan!)")

    # Simpan public key
    with open("public_key.pem", "wb") as f:
        f.write(key.publickey().export_key())
    print("✅ public_key.pem berhasil dibuat")

    print("\n⚠️  PENTING: Simpan private_key.pem dengan aman. File ini dibutuhkan untuk dekripsi data.")

if __name__ == "__main__":
    generate_rsa_keys()