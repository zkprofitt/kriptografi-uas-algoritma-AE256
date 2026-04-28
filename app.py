import streamlit as st
import mysql.connector
import base64
import time
from Crypto.Cipher import AES # Dibutuhkan untuk generate IV awal
from crypto_logic import encrypt_data, decrypt_data # Import dari file sebelah

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
    
    # Inisialisasi state agar tidak hilang saat rerun
    if 'confirm_mode' not in st.session_state:
        st.session_state.confirm_mode = False
    if 'temp_data' not in st.session_state:
        st.session_state.temp_data = {}

    # MODE 1: FORM INPUT (Muncul kalau belum klik kirim)
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
                # --- VALIDASI SEMUA KOLOM ---
                errors = []
                if not nama.strip(): errors.append("Nama Lengkap wajib diisi.")
                if not nik.isdigit() or len(nik) != 16: errors.append("NIK harus 16 digit angka.")
                if "@" not in email: errors.append("Format Email tidak valid.")
                
                gaji_clean = gaji.replace('.','').replace(',','').strip()
                nom_clean = nominal.replace('.','').replace(',','').strip()
                
                if not gaji_clean.isdigit(): errors.append("Gaji harus angka.")
                if not nom_clean.isdigit(): errors.append("Nominal harus angka.")

                if nama.lower().strip() != nama_bank_user.lower().strip():
                    errors.append("⚠️ Nama Lengkap KTP dan Nama Pemegang Akun Bank harus sama persis!")
                
                if not nama_bank_user.strip():
                    errors.append("Nama Pemegang Akun Bank wajib diisi.")

                if errors:
                    for err in errors: st.error(err)
                else:
                    # Simpan data ke session_state dan ganti mode
                    st.session_state.temp_data = {
                        'nama': nama,'nama_bank_user': nama_bank_user, 'nik': nik, 'email': email, 'hp': hp, 
                        'alamat': alamat, 'status': status, 'pekerjaan': pekerjaan,
                        'nama_pt': nama_pt, 'gaji': gaji_clean, 'darurat': darurat,
                        'bank': bank, 'nominal': nom_clean, 'tenor': tenor, 'tujuan': tujuan
                        
                    }
                    st.session_state.confirm_mode = True
                    st.rerun()

    # MODE 2: KONFIRMASI (Muncul setelah klik lanjut)
    else:
        st.warning("### ⚠️ Konfirmasi Data Pengajuan")
        d = st.session_state.temp_data
        
        col_ceka, col_cekb = st.columns(2)
        with col_ceka:
            st.write(f"Nama: **{d['nama']}**")
            st.write(f"NIK: **{d['nik']}**")
            st.write(f"HP: **{d['hp']}**")
        with col_cekb:
            st.write(f"Gaji: **{format_rupiah(d['gaji'])}**")
            st.write(f"Pinjaman: **{format_rupiah(d['nominal'])}**")
            st.write(f"Tenor: **{d['tenor']}**")

        st.info("Data ini akan langsung dienkripsi dengan AES-256 saat Anda menekan tombol simpan.")
        
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
                        # LOGIKA ENKRIPSI & INSERT (Pakai data dari st.session_state.temp_data)
                        temp_cipher = AES.new(b'ini_kunci_rahasia_32_byte_fix_ok', AES.MODE_CBC)
                        main_iv = temp_cipher.iv
                        
                        _, nik_e = encrypt_data(d['nik'], main_iv)
                        _, mail_e = encrypt_data(d['email'], main_iv)
                        _, hp_e = encrypt_data(d['hp'], main_iv)
                        _, almt_e = encrypt_data(d['alamat'], main_iv)
                        _, gaji_e = encrypt_data(d['gaji'], main_iv)
                        _, darurat_e = encrypt_data(d['darurat'], main_iv)
                        _, bank_e = encrypt_data(d['bank'], main_iv)
                        _, nom_e = encrypt_data(d['nominal'], main_iv)
                        _, n_bank_e = encrypt_data(d['nama_bank_user'], main_iv)
                        iv_savable = base64.b64encode(main_iv).decode('utf-8')

                        conn = get_db_connection()
                        cur = conn.cursor()
                        sql = """INSERT INTO pengajuan_pinjol 
                                 (nama_lengkap, pekerjaan, perusahaan, tenor, tujuan_pinjaman, status_nikah,
                                  nama_bank_user_enc, nik_enc, alamat_enc, email_enc, gaji_enc, hp_enc, kontak_darurat_enc, 
                                  rekening_enc, nominal_pinjaman_enc, iv_data) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                        cur.execute(sql, (d['nama'], d['pekerjaan'], d['nama_pt'], d['tenor'], d['tujuan'], d['status'],
                                          n_bank_e, nik_e, almt_e, mail_e, gaji_e, hp_e, darurat_e, bank_e, nom_e, iv_savable))
                        conn.commit()
                        
                        st.success("✅ BERHASIL DISIMPAN!")
                        time.sleep(1.5)
                        st.session_state.confirm_mode = False # Reset mode
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
            with st.expander(f"👤 Nasabah: {r[1]} (ID: {r[0]})"):
                col_kiri, col_kanan = st.columns(2)
                
                # Urutan kolom berdasarkan database baru:
                # 0:id, 1:nama, 2:pekerjaan, 3:pt, 4:tenor, 5:tujuan, 6:status, 
                # 7:nama_bank_user_enc, 8:nik_enc, 9:alamat_enc, 10:email_enc, 
                # 11:gaji_enc, 12:hp_enc, 13:darurat_enc, 14:rekening_enc, 
                # 15:nominal_pinjaman_enc, 16:iv_data

                with col_kiri:
                    st.markdown("### 🔐 Data Terenkripsi (DB)")
                    st.write(f"**Nama Bank Enc:** `{r[7][:30]}...`")
                    st.write(f"**NIK Enc:** `{r[8][:30]}...`")
                    st.write(f"**HP Enc:** `{r[12][:30]}...`")
                    st.write(f"**Gaji Enc:** `{r[11][:30]}...`")
                    st.write(f"**IV Data:** `{r[16]}`") # IV sekarang di indeks 16

                with col_kanan:
                    st.markdown("### 🔓 Hasil Dekripsi")
                    if st.button(f"Lihat Data Asli ID {r[0]}", key=f"dec_{r[0]}"):
                        iv = r[16] # Ambil IV dari kolom terakhir
                        
                        # Proses dekripsi dengan indeks yang sudah disesuaikan
                        d_n_bank = decrypt_data(iv, r[7])
                        d_nik = decrypt_data(iv, r[8])
                        d_almt = decrypt_data(iv, r[9])
                        d_mail = decrypt_data(iv, r[10])
                        d_gaji = format_rupiah(decrypt_data(iv, r[11]))
                        d_hp = decrypt_data(iv, r[12])
                        d_darurat = decrypt_data(iv, r[13])
                        d_rek = decrypt_data(iv, r[14])
                        d_nom = format_rupiah(decrypt_data(iv, r[15]))
                        
                        st.success("✅ Dekripsi Berhasil")
                        st.write(f"**Nama di Rekening:** {d_n_bank}")
                        st.write(f"**NIK:** {d_nik} | **HP:** {d_hp}")
                        st.write(f"**Email:** {d_mail}")
                        st.write(f"**Alamat:** {d_almt}")
                        st.write(f"**Gaji:** {d_gaji} | **Pinjaman:** {d_nom}")
                        st.write(f"**Rekening (Tujuan):** {d_rek}")
                        st.write(f"**Kontak Darurat:** {d_darurat}")
                    else:
                        st.warning("Klik tombol di atas untuk mendekripsi")

                st.markdown("---")
                if st.button(f"🗑️ Hapus Data ID {r[0]}", key=f"del_{r[0]}"):
                    if hapus_data(r[0]):
                        st.success(f"Data Berhasil Dihapus!")
                        time.sleep(1)
                        st.rerun()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")