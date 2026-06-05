import streamlit as st
import mysql.connector
import base64
import time
import os
from Crypto.Cipher import AES
from crypto_logic import encrypt_data, decrypt_data

# --- FUNGSI UTILITAS ---
def format_rupiah(angka):
    try:
        nilai = float(str(angka).replace('.', '').replace(',', '').strip())
        return f"Rp {nilai:,.0f}".replace(',', '.')
    except:
        return f"Rp {angka}"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="db_fintech"
    )

def hapus_data(id_nasabah):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pengajuan_pinjol WHERE id = %s", (id_nasabah,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Gagal menghapus: {e}")
        return False


# --- HELPER: Enkripsi satu field ---
# Format simpan: "ciphertext||RSA_key_enc"
def enc(nilai, iv):
    iv_b64, ct_b64, key_b64 = encrypt_data(nilai, iv)
    return f"{ct_b64}||{key_b64}"

# --- HELPER: Dekripsi satu field ---
def dec(gabungan, iv_b64):
    try:
        parts = gabungan.split("||")
        ct_b64, key_b64 = parts[0], parts[1]
        return decrypt_data(iv_b64, ct_b64, key_b64)
    except:
        return "Gagal membaca data"


# --- UI STREAMLIT ---
st.set_page_config(page_title="Safe-Loan - AES256+RSA", layout="wide")
st.title("🚀 Safe-Loan: Sistem Pengajuan Pinjaman Terenkripsi")
st.caption("🔐 Keamanan: AES-256-CBC + RSA-2048")
st.markdown("---")

# Cek ketersediaan file kunci RSA
if not os.path.exists("public_key.pem") or not os.path.exists("private_key.pem"):
    st.error("⚠️ File kunci RSA tidak ditemukan! Jalankan `python generate_keys.py` terlebih dahulu.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Form Pengajuan", "🖥️ Panel Admin (Database)"])

with tab1:
    st.subheader("Pendaftaran Nasabah & Pengajuan Pinjaman")

    if 'confirm_mode' not in st.session_state:
        st.session_state.confirm_mode = False
    if 'temp_data' not in st.session_state:
        st.session_state.temp_data = {}

    # MODE 1: FORM INPUT
    if not st.session_state.confirm_mode:
        with st.form("form_pinjol"):
            c1, c2 = st.columns(2)
            with c1:
                st.info("📌 Data Identitas")
                nama = st.text_input("Nama Lengkap (Sesuai KTP)")
                nik = st.text_input("NIK (16 Digit)")
                email = st.text_input("Alamat Email")
                hp = st.text_input("Nomor HP Aktif")
                alamat = st.text_area("Alamat Lengkap")
                status = st.selectbox("Status Pernikahan", ["Lajang", "Menikah", "Cerai"])

            with c2:
                st.info("💼 Data Finansial")
                pekerjaan = st.selectbox("Jenis Pekerjaan", ["Formal", "Informal"])
                nama_pt = st.text_input("Nama Perusahaan")
                gaji = st.text_input("Penghasilan Bulanan (Rp)")
                darurat = st.text_input("Kontak Darurat (Nama - No HP)")
                nama_bank_user = st.text_input("Nama Pemegang Akun Bank (Sesuai Buku Tabungan)")
                bank = st.text_input("Rekening (Bank - No Rek)")

                st.info("💰 Detail Pinjaman")
                nominal = st.text_input("Jumlah Pinjaman (Rp)")
                tenor = st.selectbox("Tenor", ["30 Hari", "3 Bulan", "6 Bulan", "12 Bulan"])
                tujuan = st.text_input("Tujuan Pinjaman")

            submit_awal = st.form_submit_button("Lanjut ke Konfirmasi")

            if submit_awal:
                errors = []
                if not nama.strip(): errors.append("Nama Lengkap wajib diisi.")
                if not nik.isdigit() or len(nik) != 16: errors.append("NIK harus 16 digit angka.")
                if "@" not in email: errors.append("Format Email tidak valid.")

                gaji_clean = gaji.replace('.', '').replace(',', '').strip()
                nom_clean  = nominal.replace('.', '').replace(',', '').strip()

                if not gaji_clean.isdigit(): errors.append("Gaji harus angka.")
                if not nom_clean.isdigit():  errors.append("Nominal harus angka.")
                if not nama_pt.strip():      errors.append("Nama Perusahaan wajib diisi.")
                if not tujuan.strip():       errors.append("Tujuan Pinjaman wajib diisi.")
                if not darurat.strip():      errors.append("Kontak Darurat wajib diisi.")
                if not bank.strip():         errors.append("Rekening wajib diisi.")

                if nama.lower().strip() != nama_bank_user.lower().strip():
                    errors.append("⚠️ Nama Lengkap KTP dan Nama Pemegang Akun Bank harus sama persis!")
                if not nama_bank_user.strip():
                    errors.append("Nama Pemegang Akun Bank wajib diisi.")

                if errors:
                    for err in errors: st.error(err)
                else:
                    st.session_state.temp_data = {
                        'nama': nama, 'nama_bank_user': nama_bank_user, 'nik': nik,
                        'email': email, 'hp': hp, 'alamat': alamat, 'status': status,
                        'pekerjaan': pekerjaan, 'nama_pt': nama_pt, 'gaji': gaji_clean,
                        'darurat': darurat, 'bank': bank, 'nominal': nom_clean,
                        'tenor': tenor, 'tujuan': tujuan
                    }
                    st.session_state.confirm_mode = True
                    st.rerun()

    # MODE 2: KONFIRMASI
    else:
        st.warning("### ⚠️ Konfirmasi Data Pengajuan")
        d = st.session_state.temp_data

        col_ceka, col_cekb = st.columns(2)
        with col_ceka:
            st.markdown("#### 👤 Data Identitas")
            st.write(f"**Nama Lengkap:** {d['nama']}")
            st.write(f"**NIK:** {d['nik']}")
            st.write(f"**Status Nikah:** {d['status']}")
            st.write(f"**HP:** {d['hp']}")
            st.write(f"**Email:** {d['email']}")
            st.write(f"**Alamat:** {d['alamat']}")

            st.markdown("#### 💼 Data Finansial")
            st.write(f"**Pekerjaan:** {d['pekerjaan']}")
            st.write(f"**Perusahaan:** {d['nama_pt']}")
            st.write(f"**Gaji:** {format_rupiah(d['gaji'])}")
            st.write(f"**Nama di Rekening:** {d['nama_bank_user']}")
            st.write(f"**Rekening:** {d['bank']}")
            st.write(f"**Kontak Darurat:** {d['darurat']}")

        with col_cekb:
            st.markdown("#### 💰 Detail Pinjaman")
            st.write(f"**Nominal Pinjaman:** {format_rupiah(d['nominal'])}")
            st.write(f"**Tenor:** {d['tenor']}")
            st.write(f"**Tujuan:** {d['tujuan']}")

        st.info("🔐 Semua data akan dienkripsi dengan **AES-256-CBC + RSA-2048** saat Anda menekan tombol simpan.")

        agree = st.checkbox("Saya menyatakan data ini benar dan bersedia diproses secara aman.")

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("⬅️ Batal"):
                st.session_state.confirm_mode = False
                st.rerun()
        with col_btn2:
            if st.button("🔥 KONFIRMASI & SIMPAN DATA"):
                if agree:
                    try:
                        with st.spinner("🔐 Mengenkripsi data dengan AES-256 + RSA-2048..."):
                            # Generate satu IV bersama untuk semua field
                            iv = os.urandom(16)
                            iv_b64 = base64.b64encode(iv).decode('utf-8')

                            nama_e      = enc(d['nama'],           iv)
                            pekerjaan_e = enc(d['pekerjaan'],      iv)
                            nama_pt_e   = enc(d['nama_pt'],        iv)
                            tenor_e     = enc(d['tenor'],          iv)
                            tujuan_e    = enc(d['tujuan'],         iv)
                            status_e    = enc(d['status'],         iv)
                            n_bank_e    = enc(d['nama_bank_user'], iv)
                            nik_e       = enc(d['nik'],            iv)
                            almt_e      = enc(d['alamat'],         iv)
                            mail_e      = enc(d['email'],          iv)
                            gaji_e      = enc(d['gaji'],           iv)
                            hp_e        = enc(d['hp'],             iv)
                            darurat_e   = enc(d['darurat'],        iv)
                            bank_e      = enc(d['bank'],           iv)
                            nom_e       = enc(d['nominal'],        iv)

                        conn = get_db_connection()
                        cur  = conn.cursor()
                        sql  = """INSERT INTO pengajuan_pinjol 
                                 (nama_display, nama_lengkap, pekerjaan, perusahaan, tenor, tujuan_pinjaman, status_nikah,
                                  nama_bank_user_enc, nik_enc, alamat_enc, email_enc, gaji_enc, hp_enc, 
                                  kontak_darurat_enc, rekening_enc, nominal_pinjaman_enc, iv_data) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                        cur.execute(sql, (
                            d['nama'],
                            nama_e, pekerjaan_e, nama_pt_e, tenor_e, tujuan_e, status_e,
                            n_bank_e, nik_e, almt_e, mail_e, gaji_e, hp_e,
                            darurat_e, bank_e, nom_e,
                            iv_b64
                        ))
                        conn.commit()
                        cur.close()
                        conn.close()

                        st.success("✅ BERHASIL DISIMPAN! Data dienkripsi dengan AES-256 + RSA-2048.")
                        time.sleep(1.5)
                        st.session_state.confirm_mode = False
                        st.session_state.temp_data    = {}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Centang persetujuan dulu!")

with tab2:
    st.subheader("🖥️ Panel Admin: Monitoring Data Terenkripsi")
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM pengajuan_pinjol ORDER BY id DESC")
        rows = cur.fetchall()

        for r in rows:
            # 0:id, 1:nama_display, 2:nama_lengkap(enc), 3:pekerjaan(enc), 4:perusahaan(enc),
            # 5:tenor(enc), 6:tujuan_pinjaman(enc), 7:status_nikah(enc),
            # 8:nama_bank_user_enc, 9:nik_enc, 10:alamat_enc, 11:email_enc,
            # 12:gaji_enc, 13:hp_enc, 14:kontak_darurat_enc, 15:rekening_enc,
            # 16:nominal_pinjaman_enc, 17:iv_data, 18:tgl_pengajuan

            nama_label = r[1]
            iv_b64     = r[17]

            def preview(val):
                return f"`{str(val)[:35]}...`"

            with st.expander(f"👤 Nasabah: {nama_label} (ID: {r[0]})"):
                col_kiri, col_kanan = st.columns(2)

                with col_kiri:
                    st.markdown("### 🔐 Data Terenkripsi (DB)")
                    st.write(f"**Nama Lengkap Enc:** {preview(r[2])}")
                    st.write(f"**Status Nikah Enc:** {preview(r[7])}")
                    st.write(f"**Pekerjaan Enc:** {preview(r[3])}")
                    st.write(f"**Perusahaan Enc:** {preview(r[4])}")
                    st.write(f"**Tenor Enc:** {preview(r[5])}")
                    st.write(f"**Tujuan Pinjaman Enc:** {preview(r[6])}")
                    st.write(f"**Nama Bank Enc:** {preview(r[8])}")
                    st.write(f"**NIK Enc:** {preview(r[9])}")
                    st.write(f"**Alamat Enc:** {preview(r[10])}")
                    st.write(f"**Email Enc:** {preview(r[11])}")
                    st.write(f"**Gaji Enc:** {preview(r[12])}")
                    st.write(f"**HP Enc:** {preview(r[13])}")
                    st.write(f"**Kontak Darurat Enc:** {preview(r[14])}")
                    st.write(f"**Rekening Enc:** {preview(r[15])}")
                    st.write(f"**Nominal Pinjaman Enc:** {preview(r[16])}")
                    st.write(f"**IV Data:** `{iv_b64}`")

                with col_kanan:
                    st.markdown("### 🔓 Hasil Dekripsi")
                    if st.button(f"Lihat Data Asli ID {r[0]}", key=f"dec_{r[0]}"):
                        with st.spinner("🔓 Mendekripsi data..."):
                            d_nama      = dec(r[2],  iv_b64)
                            d_pekerjaan = dec(r[3],  iv_b64)
                            d_pt        = dec(r[4],  iv_b64)
                            d_tenor     = dec(r[5],  iv_b64)
                            d_tujuan    = dec(r[6],  iv_b64)
                            d_status    = dec(r[7],  iv_b64)
                            d_n_bank    = dec(r[8],  iv_b64)
                            d_nik       = dec(r[9],  iv_b64)
                            d_almt      = dec(r[10], iv_b64)
                            d_mail      = dec(r[11], iv_b64)
                            d_gaji      = format_rupiah(dec(r[12], iv_b64))
                            d_hp        = dec(r[13], iv_b64)
                            d_darurat   = dec(r[14], iv_b64)
                            d_rek       = dec(r[15], iv_b64)
                            d_nom       = format_rupiah(dec(r[16], iv_b64))
                            tgl         = r[18]

                        st.success("✅ Dekripsi Berhasil")
                        st.markdown("#### 👤 Data Identitas")
                        st.write(f"**Nama Lengkap:** {d_nama}")
                        st.write(f"**NIK:** {d_nik}")
                        st.write(f"**Status Nikah:** {d_status}")
                        st.write(f"**HP:** {d_hp}")
                        st.write(f"**Email:** {d_mail}")
                        st.write(f"**Alamat:** {d_almt}")

                        st.markdown("#### 💼 Data Finansial")
                        st.write(f"**Pekerjaan:** {d_pekerjaan}")
                        st.write(f"**Perusahaan:** {d_pt}")
                        st.write(f"**Gaji:** {d_gaji}")
                        st.write(f"**Nama di Rekening:** {d_n_bank}")
                        st.write(f"**Rekening:** {d_rek}")
                        st.write(f"**Kontak Darurat:** {d_darurat}")

                        st.markdown("#### 💰 Detail Pinjaman")
                        st.write(f"**Nominal Pinjaman:** {d_nom}")
                        st.write(f"**Tenor:** {d_tenor}")
                        st.write(f"**Tujuan:** {d_tujuan}")

                        st.markdown("#### 🕒 Info Pengajuan")
                        st.write(f"**Tanggal Pengajuan:** {tgl}")
                    else:
                        st.warning("Klik tombol di atas untuk mendekripsi")

                st.markdown("---")
                if st.button(f"🗑️ Hapus Data ID {r[0]}", key=f"del_{r[0]}"):
                    if hapus_data(r[0]):
                        st.success("Data Berhasil Dihapus!")
                        time.sleep(1)
                        st.rerun()

        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")