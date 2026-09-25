import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

if not st.session_state.get("logged_in"):
    st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login.")
    st.stop()

st.set_page_config(page_title="Dashboard & Grafik", page_icon="📈", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)

st.title("📈 Dashboard Persentase & Grafik")
df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    df["tanggal_masuk"] = pd.to_datetime(df["tanggal_masuk"], errors='coerce')
    
    # Buat pilihan tahun tetap dari 2020 hingga 2030
    daftar_tahun = [y for y in range(2020, 2031)]
    tahun_sekarang = datetime.now().year
    
    # Default ke tahun berjalan jika ada di dalam rentang (2020-2030)
    if tahun_sekarang in daftar_tahun:
        idx_tahun = daftar_tahun.index(tahun_sekarang)
    else:
        idx_tahun = 0 # Default ke 2020 jika tahun sistem di luar rentang
        
    tahun_pilihan = st.selectbox("Pilih Tahun Laporan Grafik:", daftar_tahun, index=idx_tahun)
    st.markdown("---")
    
    df_tahun_ini = df[df["tanggal_masuk"].dt.year == tahun_pilihan]

    if df_tahun_ini.empty:
        st.info(f"Belum ada data pengaduan untuk tahun {tahun_pilihan}.")
    else:
        st.markdown(f"### Statistik Tahun {tahun_pilihan}")
        
        # Logika Penentuan Status Gabungan untuk Grafik
        def tentukan_status_grafik(row):
            if row['status'] == "Selesai" and row['sa_pilihan'] not in ["-", "", None]:
                return f"Selesai ({row['sa_pilihan']})"
            return row['status']
        
        df_tahun_ini["Status_Grafik"] = df_tahun_ini.apply(tentukan_status_grafik, axis=1)

        # ==========================================
        # 1. GRAFIK STATUS PENANGANAN
        # ==========================================
        st.subheader("1. Persentase Berdasarkan Status Penanganan")
        status_counts = df_tahun_ini["Status_Grafik"].value_counts().reset_index()
        status_counts.columns = ["Status", "Jumlah"]
        
        col1, col2 = st.columns([1, 2])
        col1.dataframe(status_counts, hide_index=True, use_container_width=True)
        fig_status = px.pie(status_counts, values="Jumlah", names="Status", hole=0.4)
        col2.plotly_chart(fig_status, use_container_width=True)

        st.markdown("---")
        
        # ==========================================
        # 2. GRAFIK KATEGORI
        # ==========================================
        st.subheader("2. Persentase Berdasarkan Kategori Pengaduan")
        kat_counts = df_tahun_ini["kategori"].value_counts().reset_index()
        kat_counts.columns = ["Kategori", "Jumlah"]

        col3, col4 = st.columns([1, 2])
        col3.dataframe(kat_counts, hide_index=True, use_container_width=True)
        fig_kat = px.bar(kat_counts, x="Kategori", y="Jumlah", color="Kategori", text_auto=True)
        col4.plotly_chart(fig_kat, use_container_width=True)

        st.markdown("---")

        # ==========================================
        # 3. GRAFIK PILIHAN PENYELESAIAN (BARU)
        # ==========================================
        st.subheader("3. Persentase Pilihan Penyelesaian (Khusus Kasus Selesai)")
        
        opsi_valid = ["Perjanjian Bersama (PB)", "Anjuran Tertulis", "Gugatan Hukum ke Pengadilan Hubungan Industrial (PHI)"]
        df_selesai = df_tahun_ini[df_tahun_ini["sa_pilihan"].isin(opsi_valid)]
        
        if not df_selesai.empty:
            peny_counts = df_selesai["sa_pilihan"].value_counts().reset_index()
            peny_counts.columns = ["Pilihan Penyelesaian", "Jumlah"]
            
            col5, col6 = st.columns([1, 2])
            col5.dataframe(peny_counts, hide_index=True, use_container_width=True)
            
            fig_peny = px.pie(peny_counts, values="Jumlah", names="Pilihan Penyelesaian", hole=0.4)
            col6.plotly_chart(fig_peny, use_container_width=True)
        else:
            st.info(f"Belum ada pengaduan dengan status 'Selesai' pada tahun {tahun_pilihan} untuk menampilkan grafik ini.")
else:
    st.info("Belum ada data di dalam sistem.")