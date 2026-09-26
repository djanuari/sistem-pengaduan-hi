import sqlite3
import pandas as pd
import streamlit as st
from io import BytesIO

import streamlit as st

st.set_page_config(
    page_title="Summary Report Pengaduan", page_icon="📊", layout="wide"
)

# --- CSS KUSTOM UNTUK MEMPERCANTIK TAMPILAN & FONT ---
st.markdown(
    """
    <style>
    /* Mengubah ukuran font secara umum pada teks isi/paragraf */
    p, li, span {
        font-size: 15px !important;
    }
    
    /* Memperbesar ukuran font judul utama (h1) */
    h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1f77b4;
    }
    
    /* Memperbesar ukuran font sub-judul (h2 & h3) */
    h2, h3 {
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    /* Mempercantik kotak metrik (angka ringkasan) */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 12px 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Mengatur ukuran font isi tabel agar lebih pas */
    .dataframe {
        font-size: 14px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================
# 1. SISTEM LOGIN & LOGOUT
# ==========================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

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
                st.error("Username atau password salah!")
    st.stop()

# Tombol Logout di Sidebar (Hanya muncul jika sudah masuk)
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# ==========================
# 2. INISIALISASI DATABASE
# ==========================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_pengaduan (
    no_urut INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pengaduan TEXT UNIQUE, tanggal_masuk TEXT, perihal TEXT, kategori TEXT,
    pelapor TEXT, terlapor TEXT, status TEXT, bd_ket TEXT,
    kl_tgl_surat TEXT, kl_tgl_klarifikasi TEXT, kl_ket TEXT,
    bp_tgl_pelaksanaan TEXT, bp_ket TEXT,
    tp_tgl_surat_1 TEXT, tp_tgl_1 TEXT, tp_ket_1 TEXT,
    tp_tgl_surat_2 TEXT, tp_tgl_2 TEXT, tp_ket_2 TEXT,
    tp_tgl_surat_3 TEXT, tp_tgl_3 TEXT, tp_ket_3 TEXT,
    sa_tanggal TEXT, sa_pilihan TEXT, sa_ket TEXT,
    dok_laporan TEXT, dok_selesai TEXT, catatan TEXT
)
""")
conn.commit()

# ==========================
# 3. HALAMAN SUMMARY REPORT
# ==========================
st.title("📂 Arsip Rekapitulasi Pengaduan")
st.markdown("---")

df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    # Konversi dan Ekstraksi Tanggal untuk Filter
    df["tanggal_masuk_dt"] = pd.to_datetime(df["tanggal_masuk"], errors='coerce')
    df["Tahun"] = df["tanggal_masuk_dt"].dt.year.fillna(0).astype(int).astype(str)
    
    bulan_dict = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
        7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    df["Bulan"] = df["tanggal_masuk_dt"].dt.month.map(bulan_dict)

    # Status Tampil (Singkat)
    def tentukan_status_tampil(row):
        if row['status'] == "Selesai":
            return f"Selesai: {row['sa_pilihan']}"
        return row['status']
    df["Status_Tampil"] = df.apply(tentukan_status_tampil, axis=1)

    # Filter Tahun & Bulan
    col1, col2 = st.columns(2)
    daftar_tahun = [str(y) for y in range(2020, 2031)]
    tahun_filter = col1.selectbox("Pilih Tahun:", ["Semua Tahun"] + daftar_tahun)
    
    daftar_bulan = ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan_filter = col2.selectbox("Pilih Bulan:", daftar_bulan)

    df_filtered = df.copy()
    if tahun_filter != "Semua Tahun": 
        df_filtered = df_filtered[df_filtered["Tahun"] == tahun_filter]
    if bulan_filter != "Semua Bulan": 
        df_filtered = df_filtered[df_filtered["Bulan"] == bulan_filter]

    # Tombol Download Excel
    col3, col4 = st.columns(2)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Menghapus kolom bantuan (helper) sebelum diexport
        df_filtered.drop(columns=['tanggal_masuk_dt', 'Tahun', 'Bulan', 'Status_Tampil']).to_excel(writer, index=False, sheet_name='Arsip_Pengaduan')
    excel_data = output.getvalue()
    col3.download_button("📥 Export ke Excel", data=excel_data, file_name="Arsip_Pengaduan.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Tampilan Tabel (Menampilkan Seluruh Kolom di Layar)
    st.dataframe(
        df_filtered,
        column_config={
            "no_urut": "No. Urut",
            "id_pengaduan": "ID Pengaduan",
            "tanggal_masuk": st.column_config.DateColumn("Tanggal Masuk", format="DD/MM/YYYY"),
            "perihal": "Perihal",
            "kategori": "Kategori",
            "terlapor": "Pihak Terlapor",
            "Status_Tampil": "Status Akhir",
            "sa_tanggal": st.column_config.DateColumn("Tanggal Selesai", format="DD/MM/YYYY"),
            "dok_selesai": st.column_config.LinkColumn("Unduh Dokumen"),
        },
        use_container_width=True,
        hide_index=True,
        # MASUKKAN KOLOM YANG INGIN DITAMPILKAN DI SINI:
        column_order=(
            "no_urut",
            "id_pengaduan",
            "tanggal_masuk",
            "kategori",
            "perihal",
            "terlapor",
            "Status_Tampil",
            "dok_selesai",
        ),
    )
else:
    st.info("Belum ada data pengaduan. Silakan isi melalui menu di sidebar.")
