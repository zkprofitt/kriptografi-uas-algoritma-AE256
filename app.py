import streamlit as st
import mysql.connector
import base64
import time
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
        query = "DELETE FROM pengajuan_pinjol WHERE id = %s"
        cursor.execute(query, (id_nasabah,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Gagal menghapus: {e}")
        return False


# --- UI STREAMLIT ---
st.set_page_config(page_title="Pinjol Pro - AES256", layout="wide")
st.title("🚀 Safe-Loan: Sistem Pengajuan Pinjaman Terenkripsi")
st.markdown("---")

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
                nom_clean = nominal.replace('.', '').replace(',', '').strip()

                if not gaji_clean.isdigit(): errors.append("Gaji harus angka.")
                if not nom_clean.isdigit(): errors.append("Nominal harus angka.")
                if not nama_pt.strip(): errors.append("Nama Perusahaan wajib diisi.")
                if not tujuan.strip(): errors.append("Tujuan Pinjaman wajib diisi.")
                if not darurat.strip(): errors.append("Kontak Darurat wajib diisi.")
                if not bank.strip(): errors.append("Rekening wajib diisi.")

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

        st.info("Semua data (termasuk nama, pekerjaan, tenor, dll) akan dienkripsi dengan AES-256 saat Anda menekan tombol simpan.")

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
                        # Generate satu IV untuk semua field
                        temp_cipher = AES.new(b'ini_kunci_rahasia_32_byte_fix_ok', AES.MODE_CBC)
                        main_iv = temp_cipher.iv

                        # Enkripsi SEMUA field (termasuk yang sebelumnya plaintext)
                        _, nama_e      = encrypt_data(d['nama'], main_iv)
                        _, pekerjaan_e = encrypt_data(d['pekerjaan'], main_iv)
                        _, nama_pt_e   = encrypt_data(d['nama_pt'], main_iv)
                        _, tenor_e     = encrypt_data(d['tenor'], main_iv)
                        _, tujuan_e    = encrypt_data(d['tujuan'], main_iv)
                        _, status_e    = encrypt_data(d['status'], main_iv)
                        _, n_bank_e    = encrypt_data(d['nama_bank_user'], main_iv)
                        _, nik_e       = encrypt_data(d['nik'], main_iv)
                        _, almt_e      = encrypt_data(d['alamat'], main_iv)
                        _, mail_e      = encrypt_data(d['email'], main_iv)
                        _, gaji_e      = encrypt_data(d['gaji'], main_iv)
                        _, hp_e        = encrypt_data(d['hp'], main_iv)
                        _, darurat_e   = encrypt_data(d['darurat'], main_iv)
                        _, bank_e      = encrypt_data(d['bank'], main_iv)
                        _, nom_e       = encrypt_data(d['nominal'], main_iv)

                        iv_savable = base64.b64encode(main_iv).decode('utf-8')

                        conn = get_db_connection()
                        cur = conn.cursor()

                        # Simpan nama_display (plaintext) untuk label expander
                        # Semua kolom lain sudah terenkripsi
                        sql = """INSERT INTO pengajuan_pinjol 
                                 (nama_display, nama_lengkap, pekerjaan, perusahaan, tenor, tujuan_pinjaman, status_nikah,
                                  nama_bank_user_enc, nik_enc, alamat_enc, email_enc, gaji_enc, hp_enc, 
                                  kontak_darurat_enc, rekening_enc, nominal_pinjaman_enc, iv_data) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                        cur.execute(sql, (
                            d['nama'],      # nama_display: plaintext untuk label
                            nama_e,         # nama_lengkap: terenkripsi
                            pekerjaan_e,    # pekerjaan: terenkripsi
                            nama_pt_e,      # perusahaan: terenkripsi
                            tenor_e,        # tenor: terenkripsi
                            tujuan_e,       # tujuan_pinjaman: terenkripsi
                            status_e,       # status_nikah: terenkripsi
                            n_bank_e, nik_e, almt_e, mail_e, gaji_e, hp_e,
                            darurat_e, bank_e, nom_e,
                            iv_savable
                        ))
                        conn.commit()
                        cur.close()
                        conn.close()

                        st.success("✅ BERHASIL DISIMPAN! Semua data terenkripsi.")
                        time.sleep(1.5)
                        st.session_state.confirm_mode = False
                        st.session_state.temp_data = {}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Centang persetujuan dulu!")

with tab2:
    st.subheader("🖥️ Panel Admin: Monitoring Data Terenkripsi")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pengajuan_pinjol ORDER BY id DESC")
        rows = cur.fetchall()

        for r in rows:
            # Urutan kolom setelah ALTER TABLE:
            # 0:id, 1:nama_display, 2:nama_lengkap(enc), 3:pekerjaan(enc), 4:perusahaan(enc),
            # 5:tenor(enc), 6:tujuan_pinjaman(enc), 7:status_nikah(enc),
            # 8:nama_bank_user_enc, 9:nik_enc, 10:alamat_enc, 11:email_enc,
            # 12:gaji_enc, 13:hp_enc, 14:kontak_darurat_enc, 15:rekening_enc,
            # 16:nominal_pinjaman_enc, 17:iv_data, 18:tgl_pengajuan

            nama_label = r[1]  # nama_display (plaintext)
            iv = r[17]         # iv_data

            with st.expander(f"👤 Nasabah: {nama_label}"):
                col_kiri, col_kanan = st.columns(2)

                with col_kiri:
                    st.markdown("### 🔐 Data Terenkripsi (DB)")
                    st.write(f"**Nama Lengkap Enc:** `{str(r[2])[:30]}...`")
                    st.write(f"**NIK Enc:** `{str(r[9])[:30]}...`")
                    st.write(f"**Status Nikah Enc:** `{str(r[7])[:30]}...`")
                    st.write(f"**HP Enc:** `{str(r[13])[:30]}...`")
                    st.write(f"**Email Enc:** `{str(r[11])[:30]}...`")
                    st.write(f"**Pekerjaan Enc:** `{str(r[3])[:30]}...`")
                    st.write(f"**Perusahaan Enc:** `{str(r[4])[:30]}...`")
                    st.write(f"**Gaji Enc:** `{str(r[12])[:30]}...`")
                    st.write(f"**Nama Bank Enc:** `{str(r[8])[:30]}...`")
                    st.write(f"**Rekening Enc:** `{str(r[15])[:30]}...`")
                    st.write(f"**Kontak Darurat Enc:** `{str(r[14])[:30]}...`")
                    st.write(f"**Nominal Pinjaman Enc:** `{str(r[16])[:30]}...`")
                    st.write(f"**Tenor Enc:** `{str(r[5])[:30]}...`")
                    st.write(f"**Tujuan Pinjaman Enc:** `{str(r[6])[:30]}...`")
                    st.write(f"**IV Data:** `{iv}`")

                with col_kanan:
                    st.markdown("### 🔓 Hasil Dekripsi")
                    if st.button(f"Lihat Data Asli ID {r[0]}", key=f"dec_{r[0]}"):
                        d_nama      = decrypt_data(iv, r[2])
                        d_pekerjaan = decrypt_data(iv, r[3])
                        d_pt        = decrypt_data(iv, r[4])
                        d_tenor     = decrypt_data(iv, r[5])
                        d_tujuan    = decrypt_data(iv, r[6])
                        d_status    = decrypt_data(iv, r[7])
                        d_n_bank    = decrypt_data(iv, r[8])
                        d_nik       = decrypt_data(iv, r[9])
                        d_almt      = decrypt_data(iv, r[10])
                        d_mail      = decrypt_data(iv, r[11])
                        d_gaji      = format_rupiah(decrypt_data(iv, r[12]))
                        d_hp        = decrypt_data(iv, r[13])
                        d_darurat   = decrypt_data(iv, r[14])
                        d_rek       = decrypt_data(iv, r[15])
                        d_nom       = format_rupiah(decrypt_data(iv, r[16]))
                        tgl         = r[18]  # tgl_pengajuan (plaintext TIMESTAMP)

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
                if st.button(f"🗑️ Hapus Data ID ", key=f"del_{r[0]}"):
                    if hapus_data(r[0]):
                        st.success(f"Data Berhasil Dihapus!")
                        time.sleep(1)
                        st.rerun()

        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")