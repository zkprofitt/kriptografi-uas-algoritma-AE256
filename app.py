import streamlit as st
import mysql.connector
import base64
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
            nama_pt = st.text_input("Nama Perusahaan/Usaha")
            gaji = st.text_input("Penghasilan Bulanan (Rp)")
            darurat = st.text_input("Kontak Darurat (Nama - No HP)")
            bank = st.text_input("Rekening (Nama Bank - No Rek)")
            
            st.info("💰 Detail Pinjaman")
            nominal = st.text_input("Jumlah Pinjaman (Rp)")
            tenor = st.selectbox("Tenor", ["30 Hari", "3 Bulan", "6 Bulan", "12 Bulan"])
            tujuan = st.text_input("Tujuan Pinjaman")

        if st.form_submit_button("Kirim Pengajuan"):
            if not nama or not nik or not nominal:
                st.error("Data Nama, NIK, dan Nominal Pinjaman wajib diisi!")
            else:
                gaji_clean = gaji.replace('.','').replace(',','').strip()
                nom_clean = nominal.replace('.','').replace(',','').strip()
                
                # Generate IV utama untuk baris ini
                temp_cipher = AES.new(b'ini_kunci_rahasia_32_byte_fix_ok', AES.MODE_CBC)
                main_iv = temp_cipher.iv
                
                # Proses Enkripsi Field Sensitif
                _, nik_e = encrypt_data(nik, main_iv)
                _, mail_e = encrypt_data(email, main_iv)
                _, hp_e = encrypt_data(hp, main_iv)
                _, almt_e = encrypt_data(alamat, main_iv)
                _, gaji_e = encrypt_data(gaji_clean, main_iv)
                _, darurat_e = encrypt_data(darurat, main_iv)
                _, bank_e = encrypt_data(bank, main_iv)
                _, nom_e = encrypt_data(nom_clean, main_iv)
                
                iv_savable = base64.b64encode(main_iv).decode('utf-8')

                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    sql = """INSERT INTO pengajuan_pinjol 
                             (nama_lengkap, pekerjaan, perusahaan, tenor, tujuan_pinjaman, status_nikah,
                              nik_enc, alamat_enc, email_enc, gaji_enc, hp_enc, kontak_darurat_enc, 
                              rekening_enc, nominal_pinjaman_enc, iv_data) 
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    cur.execute(sql, (nama, pekerjaan, nama_pt, tenor, tujuan, status,
                                      nik_e, almt_e, mail_e, gaji_e, hp_e, darurat_e, bank_e, nom_e, iv_savable))
                    conn.commit()
                    st.success("✅ Sukses! Data Anda telah dienkripsi dan dikirim ke server.")
                except Exception as e:
                    st.error(f"Koneksi Database Gagal: {e}")

with tab2:
    st.subheader("🖥️ Panel Admin: Monitoring Data Terenkripsi")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pengajuan_pinjol ORDER BY id DESC")
        rows = cur.fetchall()
        
        for r in rows:
            with st.expander(f"👤 Nasabah: {r[1]} (ID: {r[0]})"):
                # Kita bagi jadi dua kolom besar
                col_kiri, col_kanan = st.columns(2)
                
                with col_kiri:
                    st.markdown("### 🔐 Data Terenkripsi (DB)")
                    # Menampilkan ciphertext yang dipotong (truncated) biar rapi
                    st.write(f"**NIK Enc:** `{r[7][:30]}...`")
                    st.write(f"**Email Enc:** `{r[9][:30]}...`")
                    st.write(f"**HP Enc:** `{r[11][:30]}...`")
                    st.write(f"**Alamat Enc:** `{r[8][:30]}...`")
                    st.write(f"**Gaji Enc:** `{r[10][:30]}...`")
                    st.write(f"**Pinjaman Enc:** `{r[14][:30]}...`")
                    st.write(f"**Rekening Enc:** `{r[13][:30]}...`")
                    st.write(f"**IV Data:** `{r[15]}`") # Menampilkan IV baris ini
                    

                with col_kanan:
                    st.markdown("### 🔓 Hasil Dekripsi")
                    if st.button(f"Lihat Data Asli ID {r[0]}", key=f"dec_{r[0]}"):
                        # Proses dekripsi semua field menggunakan IV dari r[15]
                        d_nik = decrypt_data(r[15], r[7])
                        d_mail = decrypt_data(r[15], r[9])
                        d_hp = decrypt_data(r[15], r[11])
                        d_almt = decrypt_data(r[15], r[8])
                        d_gaji = format_rupiah(decrypt_data(r[15], r[10]))
                        d_nom = format_rupiah(decrypt_data(r[15], r[14]))
                        d_rek = decrypt_data(r[15], r[13])
                        d_darurat = decrypt_data(r[15], r[12])
                        
                        # Tampilan hasil rapi dalam box success
                        st.success("✅ Dekripsi Berhasil")
                        st.write(f"**NIK:** {d_nik}")
                        st.write(f"**Email:** {d_mail}")
                        st.write(f"**No. HP:** {d_hp}")
                        st.write(f"**Alamat:** {d_almt}")
                        st.write(f"**Gaji:** {d_gaji}")
                        st.write(f"**Nominal Pinjam:** {d_nom}")
                        st.write(f"**Rekening:** {d_rek}")
                        st.write(f"**Kontak Darurat:** {d_darurat}")
                    else:
                        st.warning("Klik tombol di atas untuk mendekripsi data")

                # --- TOMBOL HAPUS (Taruh di paling bawah expander) ---
                st.markdown("---")
                if st.button(f"🗑️ Hapus Data ID {r[0]}", key=f"del_{r[0]}"):
                    if hapus_data(r[0]):
                        st.success(f"Data ID {r[0]} Berhasil Dihapus!")
                        st.rerun() # Ini penting biar tampilan langsung update (data ilang)
                        cur.close()
                        conn.close()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")