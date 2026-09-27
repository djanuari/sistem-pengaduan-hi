import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Silakan login terlebih dahulu melalui halaman utama.")
    st.stop()

st.set_page_config(page_title="Dashboard & Grafik", page_icon="📈", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)

st.title("📈 Dashboard Persentase & Grafik")
df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    df["tanggal_masuk"] = pd.to_datetime(df["tanggal_masuk"], errors='coerce')
    
    # Pilihan Tahun (2020 - 2030)
    daftar_tahun = [y for y in range(2020, 2031)]
    tahun_sekarang = datetime.now().year
    idx_tahun = daftar_tahun.index(tahun_sekarang) if tahun_sekarang in daftar_tahun else 0
        
    tahun_pilihan = st.selectbox("Pilih Tahun Laporan Grafik:", daftar_tahun, index=idx_tahun)
    st.markdown("---")
    
    df_tahun_ini = df[df["tanggal_masuk"].dt.year == tahun_pilihan]

    if df_tahun_ini.empty:
        st.info(f"Belum ada data pengaduan untuk tahun {tahun_pilihan}.")
    else:
        st.markdown(f"### Statistik Tahun {tahun_pilihan}")
        
        # Ringkasan Metrik Angka
        total_periode = len(df_tahun_ini)
        selesai_periode = len(df_tahun_ini[df_tahun_ini["status"] == "Selesai"])
        proses_periode = total_periode - selesai_periode
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Kasus", f"{total_periode}")
        m2.metric("Dalam Proses", f"{proses_periode}")
        m3.metric("Selesai", f"{selesai_periode}")
        
        st.markdown("---")

        # ==========================================
        # 1. GRAFIK TREN BULANAN (Lingkaran / Pie)
        # ==========================================
        st.subheader("1. Persentase Pengaduan Per Bulan")
        nama_bulan_dict = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 
            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        df_tahun_ini["Bulan_Angka"] = df_tahun_ini["tanggal_masuk"].dt.month
        df_tahun_ini["Nama_Bulan"] = df_tahun_ini["Bulan_Angka"].map(nama_bulan_dict)
        
        bulan_counts = df_tahun_ini.groupby(["Bulan_Angka", "Nama_Bulan"]).size().reset_index(name="Jumlah")
        bulan_counts = bulan_counts.sort_values("Bulan_Angka")
        
        col_b1, col_b2 = st.columns([1, 2])
        col_b1.dataframe(bulan_counts[["Nama_Bulan", "Jumlah"]], hide_index=True, use_container_width=True)
        
        fig_bulan = px.pie(bulan_counts, values="Jumlah", names="Nama_Bulan", hole=0.4)
        col_b2.plotly_chart(fig_bulan, use_container_width=True)

        st.markdown("---")

        def tentukan_status_grafik(row):
            if row['status'] == "Selesai" and row['sa_pilihan'] not in ["-", "", None]:
                return f"Selesai ({row['sa_pilihan']})"
            return row['status']
        
        df_tahun_ini["Status_Grafik"] = df_tahun_ini.apply(tentukan_status_grafik, axis=1)

        # ==========================================
        # 2. GRAFIK STATUS PENANGANAN (Lingkaran / Pie)
        # ==========================================
        st.subheader("2. Persentase Berdasarkan Status Penanganan")
        status_counts = df_tahun_ini["Status_Grafik"].value_counts().reset_index()
        status_counts.columns = ["Status", "Jumlah"]
        
        col1, col2 = st.columns([1, 2])
        col1.dataframe(status_counts, hide_index=True, use_container_width=True)
        fig_status = px.pie(status_counts, values="Jumlah", names="Status", hole=0.4)
        col2.plotly_chart(fig_status, use_container_width=True)

        st.markdown("---")
        
        # ==========================================
        # 3. GRAFIK KATEGORI (Lingkaran / Pie)
        # ==========================================
        st.subheader("3. Persentase Berdasarkan Kategori Pengaduan")
        kat_counts = df_tahun_ini["kategori"].value_counts().reset_index()
        kat_counts.columns = ["Kategori", "Jumlah"]

        col3, col4 = st.columns([1, 2])
        col3.dataframe(kat_counts, hide_index=True, use_container_width=True)
        
        fig_kat = px.pie(kat_counts, values="Jumlah", names="Kategori", hole=0.4)
        col4.plotly_chart(fig_kat, use_container_width=True)

        st.markdown("---")

        # ==========================================
        # 4. GRAFIK PILIHAN PENYELESAIAN (Lingkaran / Pie)
        # ==========================================
        st.subheader("4. Persentase Pilihan Penyelesaian (Khusus Kasus Selesai)")
        
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
