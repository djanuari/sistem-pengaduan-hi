import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

if not st.session_state.get("logged_in"):
    st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login.")
    st.stop()

st.set_page_config(page_title="Dashboard & Grafik", page_icon="📈", layout="wide")

# --- CSS KUSTOM UNIVERSAL AGAR TAMPILANNYA SERAGAM ---
st.markdown("""
    <style>
    p, label, span, .stTextInput, .stSelectbox {
        font-size: 15px !important;
    }
    h1 {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #2c3e50 !important;
    }
    h2, h3 {
        font-size: 19px !important;
        font-weight: 600 !important;
        color: #34495e !important;
    }
    .stSelectbox select {
        border-radius: 6px !important;
    }
    div[data-testid="metric-container"] {
        background-color: #fdfefe;
        border: 1px solid #d5dbdb;
        padding: 10px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

conn = sqlite3.connect("database.db", check_same_thread=False)

st.title("📈 Dashboard Persentase & Grafik")
df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    df["tanggal_masuk"] = pd.to_datetime(df["tanggal_masuk"], errors='coerce')
    
    # Layout Filter Tahun & Bulan Berdampingan
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        daftar_tahun = [y for y in range(2020, 2031)]
        tahun_sekarang = datetime.now().year
        idx_tahun = daftar_tahun.index(tahun_sekarang) if tahun_sekarang in daftar_tahun else 0
        tahun_pilihan = st.selectbox("Pilih Tahun Laporan:", daftar_tahun, index=idx_tahun)
        
    with col_f2:
        nama_bulan_dict = {
            0: "Semua Bulan (1 Tahun Penuh)",
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 
            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        pilihan_bulan = st.selectbox("Pilih Bulan Spesifik:", options=list(nama_bulan_dict.keys()), format_func=lambda x: nama_bulan_dict[x])

    st.markdown("---")
    
    # Filter Berdasarkan Tahun Terlebih Dahulu
    df_filtered = df[df["tanggal_masuk"].dt.year == tahun_pilihan]

    # Jika user memilih bulan spesifik (bukan 0/Semua Bulan), filter lagi berdasarkan bulan
    if pilihan_bulan != 0:
        df_filtered = df_filtered[df_filtered["tanggal_masuk"].dt.month == pilihan_bulan]
        label_waktu = f"Bulan {nama_bulan_dict[pilihan_bulan]} {tahun_pilihan}"
    else:
        label_waktu = f"Tahun {tahun_pilihan} (Semua Bulan)"

    if df_filtered.empty:
        st.info(f"Belum ada data pengaduan untuk periode {label_waktu}.")
    else:
        st.markdown(f"### Statistik Periode: {label_waktu}")
        
        total_periode = len(df_filtered)
        selesai_periode = len(df_filtered[df_filtered["status"] == "Selesai"])
        proses_periode = total_periode - selesai_periode
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Kasus", f"{total_periode}")
        m2.metric("Dalam Proses", f"{proses_periode}")
        m3.metric("Selesai", f"{selesai_periode}")
        
        st.markdown("---")
        
        # Jika user memilih "Semua Bulan", tampilkan grafik proporsi per bulan berbentuk lingkaran
        if pilihan_bulan == 0:
            st.subheader("4. Proporsi Pengaduan Berdasarkan Bulan")
            df_filtered["Bulan_Angka"] = df_filtered["tanggal_masuk"].dt.month
            df_filtered["Nama_Bulan"] = df_filtered["Bulan_Angka"].map(nama_bulan_dict)
            
            bulan_counts = df_filtered.groupby(["Bulan_Angka", "Nama_Bulan"]).size().reset_index(name="Jumlah")
            bulan_counts = bulan_counts.sort_values("Bulan_Angka")
            
            col_b1, col_b2 = st.columns([1, 2])
            col_b1.dataframe(bulan_counts[["Nama_Bulan", "Jumlah"]], hide_index=True, use_container_width=True)
            
            # Diubah menjadi grafik lingkaran (pie/donut chart)
            fig_bulan = px.pie(
                bulan_counts, 
                values="Jumlah", 
                names="Nama_Bulan", 
                hole=0.4
            )
            col_b2.plotly_chart(fig_bulan, use_container_width=True)
            st.markdown("---")

        def tentukan_status_grafik(row):
            if row['status'] == "Selesai" and row['sa_pilihan'] not in ["-", "", None]:
                return f"Selesai ({row['sa_pilihan']})"
            return row['status']
        
        df_filtered["Status_Grafik"] = df_filtered.apply(tentukan_status_grafik, axis=1)

        # ==========================================
        # 1. GRAFIK STATUS PENANGANAN (LINGKARAN)
        # ==========================================
        st.subheader("1. Persentase Berdasarkan Status Penanganan")
        status_counts = df_filtered["Status_Grafik"].value_counts().reset_index()
        status_counts.columns = ["Status", "Jumlah"]
        
        col1, col2 = st.columns([1, 2])
        col1.dataframe(status_counts, hide_index=True, use_container_width=True)
        fig_status = px.pie(status_counts, values="Jumlah", names="Status", hole=0.4)
        col2.plotly_chart(fig_status, use_container_width=True)

        st.markdown("---")
        
        # ==========================================
        # 2. GRAFIK KATEGORI (LINGKARAN)
        # ==========================================
        st.subheader("2. Persentase Berdasarkan Kategori Pengaduan")
        kat_counts = df_filtered["kategori"].value_counts().reset_index()
        kat_counts.columns = ["Kategori", "Jumlah"]

        col3, col4 = st.columns([1, 2])
        col3.dataframe(kat_counts, hide_index=True, use_container_width=True)
        fig_kat = px.pie(kat_counts, values="Jumlah", names="Kategori", hole=0.4)
        col4.plotly_chart(fig_kat, use_container_width=True)

        st.markdown("---")

        # ==========================================
        # 3. GRAFIK PILIHAN PENYELESAIAN (LINGKARAN)
        # ==========================================
        st.subheader("3. Persentase Pilihan Penyelesaian (Khusus Kasus Selesai)")
        
        opsi_valid = ["Perjanjian Bersama (PB)", "Anjuran Tertulis", "Gugatan Hukum ke Pengadilan Hubungan Industrial (PHI)"]
        df_selesai = df_filtered[df_filtered["sa_pilihan"].isin(opsi_valid)]
        
        if not df_selesai.empty:
            peny_counts = df_selesai["sa_pilihan"].value_counts().reset_index()
            peny_counts.columns = ["Pilihan Penyelesaian", "Jumlah"]
            
            col5, col6 = st.columns([1, 2])
            col5.dataframe(peny_counts, hide_index=True, use_container_width=True)
            fig_peny = px.pie(peny_counts, values="Jumlah", names="Pilihan Penyelesaian", hole=0.4)
            col6.plotly_chart(fig_peny, use_container_width=True)
        else:
            st.info(f"Belum ada pengaduan dengan status 'Selesai' pada periode ini.")
else:
    st.info("Belum ada data di dalam sistem.")
