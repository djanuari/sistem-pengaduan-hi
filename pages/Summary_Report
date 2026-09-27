import sqlite3
import pandas as pd
import streamlit as st

# 1. Wajib ada: Inisialisasi dan Penjaga Sesi Login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 2. Jika belum login, tampilkan form login
if not st.session_state["logged_in"]:
    st.title("🔐 Login Sistem Informasi HI")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Login")
        
        if submit_login:
            if username == "admin" and password == "admin123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Username atau Password salah!")
    st.stop() # Hentikan agar halaman utama tidak terbuka sebelum login

# Tombol Logout di Sidebar setelah berhasil masuk
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

st.set_page_config(page_title="Summary Report Pengaduan", page_icon="📊", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)

st.title("📊 Summary Report & Rekapitulasi Pengaduan")
df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    st.markdown("### Daftar Seluruh Pengaduan Masuk")
    
    # Filter pencarian sederhana
    pencarian = st.text_input("🔍 Cari berdasarkan ID, Pelapor, atau Terlapor:")
    if pencarian:
        df_tampil = df[
            df['id_pengaduan'].str.contains(pencarian, case=False, na=False) |
            df['pelapor'].str.contains(pencarian, case=False, na=False) |
            df['terlapor'].str.contains(pencarian, case=False, na=False)
        ]
    else:
        df_tampil = df

    # Menampilkan Tabel Rekapitulasi Utama
    st.dataframe(df_tampil, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🔎 Lihat Detail Lengkap Berdasarkan ID Pengaduan")
    
    # Pilihan ID untuk melihat detail data secara spesifik
    list_id = df["id_pengaduan"].tolist()
    pilih_id = st.selectbox("Pilih ID Pengaduan untuk melihat rincian lengkap:", list_id)
    
    if pilih_id:
        data_detail = df[df["id_pengaduan"] == pilih_id].iloc[0]
        
        # Tampilkan rincian data dalam bentuk kolom rapi
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**ID Pengaduan:** {data_detail['id_pengaduan']}")
            st.markdown(f"**Tanggal Masuk:** {data_detail['tanggal_masuk']}")
            st.markdown(f"**Kategori:** {data_detail['kategori']}")
            st.markdown(f"**Pelapor:** {data_detail['pelapor']} ({data_detail.get('no_telp', '-')})")
            st.markdown(f"**Alamat Pelapor:** {data_detail.get('alamat', '-')}")
        with col_d2:
            st.markdown(f"**Terlapor:** {data_detail['terlapor']} ({data_detail.get('no_telp_terlapor', '-')})")
            st.markdown(f"**Alamat Terlapor:** {data_detail.get('alamat_terlapor', '-')}")
            st.markdown(f"**Mediator:** {data_detail.get('mediator', '-')}")
            st.markdown(f"**Status Saat Ini:** `{data_detail['status']}`")
            
        st.markdown(f"**Perihal:** {data_detail['perihal']}")
        
        # Menampilkan Link Dokumen agar bisa diklik langsung
        st.markdown("---")
        st.markdown("📂 **Tautan Dokumen Terkait:**")
        
        link_lap = data_detail.get('dok_laporan', '')
        link_sel = data_detail.get('dok_selesai', '')
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if link_lap and str(link_lap).startswith("http"):
                st.markdown(f"- [Buka Dokumen Laporan]({link_lap})")
            else:
                st.markdown("- Dokumen Laporan: *Belum diunggah / Bukan link valid*")
        with col_l2:
            if link_sel and str(link_sel).startswith("http"):
                st.markdown(f"- [Buka Laporan Selesai]({link_sel})")
            else:
                st.markdown("- Laporan Selesai: *Belum diunggah / Bukan link valid*")

else:
    st.info("Belum ada data pengaduan yang tersimpan di dalam database.")

# Menu Sidebar untuk Backup Database
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Pencadangan Data")
try:
    with open("database.db", "rb") as f:
        db_bytes = f.read()
    st.sidebar.download_button(
        label="📥 Unduh Backup Database",
        data=db_bytes,
        file_name="database_backup.db",
        mime="application/octet-stream"
    )
except FileNotFoundError:
    pass
