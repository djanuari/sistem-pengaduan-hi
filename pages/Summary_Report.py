import sqlite3
import pandas as pd
import streamlit as st
from io import BytesIO
import datetime

# Import reportlab untuk fitur PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Sistem Informasi Pengaduan HI", page_icon="🏢", layout="wide")

# ==========================
# 1. SISTEM LOGIN
# ==========================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Login Sistem Informasi HI")
    st.write("Silakan masukkan username dan password untuk masuk ke dalam sistem.")
    
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

# ==========================
# 2. TOMBOL LOGOUT & BACKUP DI SIDEBAR
# ==========================
with st.sidebar:
    st.write(f"Halo, **Admin**")
    if st.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.rerun()
    
    st.markdown("---")
    st.subheader("⚙️ Backup Data")
    try:
        with open("database.db", "rb") as f:
            st.download_button(
                label="📥 Unduh Backup Database",
                data=f,
                file_name="database_backup.db",
                mime="application/octet-stream"
            )
    except FileNotFoundError:
        st.caption("Database belum aktif.")

# ==========================
# 3. INISIALISASI & MIGRASI DATABASE OTOMATIS
# ==========================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_pengaduan (
    no_urut INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pengaduan TEXT UNIQUE
)
""")
conn.commit()

kolom_baru = [
    ("tanggal_masuk", "TEXT"), ("perihal", "TEXT"), ("kategori", "TEXT"),
    ("pelapor", "TEXT"), ("terlapor", "TEXT"), ("alamat", "TEXT"), ("no_telp", "TEXT"),
    ("alamat_terlapor", "TEXT"), ("no_telp_terlapor", "TEXT"), ("mediator", "TEXT"),
    ("status", "TEXT"), ("bd_ket", "TEXT"), ("kl_tgl_surat", "TEXT"),
    ("kl_tgl_klarifikasi", "TEXT"), ("kl_ket", "TEXT"), ("bp_tgl_pelaksanaan", "TEXT"),
    ("bp_ket", "TEXT"), ("tp_tgl_surat_1", "TEXT"), ("tp_tgl_1", "TEXT"), ("tp_ket_1", "TEXT"),
    ("tp_tgl_surat_2", "TEXT"), ("tp_tgl_2", "TEXT"), ("tp_ket_2", "TEXT"),
    ("tp_tgl_surat_3", "TEXT"), ("tp_tgl_3", "TEXT"), ("tp_ket_3", "TEXT"),
    ("sa_tanggal", "TEXT"), ("sa_pilihan", "TEXT"), ("sa_ket", "TEXT"),
    ("dok_laporan", "TEXT"), ("dok_selesai", "TEXT"), ("catatan", "TEXT")
]

for col_nama, col_tipe in kolom_baru:
    try:
        cursor.execute(f"ALTER TABLE tabel_pengaduan ADD COLUMN {col_nama} {col_tipe}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# Fungsi Generator PDF
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#1f2937")
    )
    
    story.append(Paragraph("<b>PEMERINTAH KOTA KENDARI</b>", title_style))
    story.append(Paragraph("<b>LAPORAN DETAIL PENGADUAN HUBUNGAN INDUSTRIAL</b>", title_style))
    story.append(Spacer(1, 15))
    
    def format_val(val):
        if not val or str(val) == "nan" or str(val).strip() == "":
            return "-"
        return str(val)

    data_tabel = [
        [Paragraph("<b>ID Pengaduan</b>", styles['Normal']), Paragraph(format_val(row.get('id_pengaduan')), styles['Normal'])],
        [Paragraph("<b>Tanggal Masuk</b>", styles['Normal']), Paragraph(format_val(row.get('tanggal_masuk')), styles['Normal'])],
        [Paragraph("<b>Kategori</b>", styles['Normal']), Paragraph(format_val(row.get('kategori')), styles['Normal'])],
        [Paragraph("<b>Perihal</b>", styles['Normal']), Paragraph(format_val(row.get('perihal')), styles['Normal'])],
        [Paragraph("<b>Pelapor / Pemohon</b>", styles['Normal']), Paragraph(format_val(row.get('pelapor')), styles['Normal'])],
        [Paragraph("<b>Alamat Pelapor</b>", styles['Normal']), Paragraph(format_val(row.get('alamat')), styles['Normal'])],
        [Paragraph("<b>No. Telp Pelapor</b>", styles['Normal']), Paragraph(format_val(row.get('no_telp')), styles['Normal'])],
        [Paragraph("<b>Terlapor / Perusahaan</b>", styles['Normal']), Paragraph(format_val(row.get('terlapor')), styles['Normal'])],
        [Paragraph("<b>Alamat Terlapor</b>", styles['Normal']), Paragraph(format_val(row.get('alamat_terlapor')), styles['Normal'])],
        [Paragraph("<b>No. Telp Terlapor</b>", styles['Normal']), Paragraph(format_val(row.get('no_telp_terlapor')), styles['Normal'])],
        [Paragraph("<b>Mediator</b>", styles['Normal']), Paragraph(format_val(row.get('mediator')), styles['Normal'])],
        [Paragraph("<b>Status Berjalan</b>", styles['Normal']), Paragraph(format_val(row.get('status')), styles['Normal'])],
        [Paragraph("<b>Keterangan Belum Diproses</b>", styles['Normal']), Paragraph(format_val(row.get('bd_ket')), styles['Normal'])],
        [Paragraph("<b>Klarifikasi (Tgl Surat / Tgl / Ket)</b>", styles['Normal']), Paragraph(f"Surat: {format_val(row.get('kl_tgl_surat'))} | Tgl: {format_val(row.get('kl_tgl_klarifikasi'))} | Ket: {format_val(row.get('kl_ket'))}", styles['Normal'])],
        [Paragraph("<b>Bipartit (Tgl / Ket)</b>", styles['Normal']), Paragraph(f"Tgl: {format_val(row.get('bp_tgl_pelaksanaan'))} | Ket: {format_val(row.get('bp_ket'))}", styles['Normal'])],
        [Paragraph("<b>Mediasi 1 (Surat / Tgl / Ket)</b>", styles['Normal']), Paragraph(f"Surat: {format_val(row.get('tp_tgl_surat_1'))} | Tgl: {format_val(row.get('tp_tgl_1'))} | Ket: {format_val(row.get('tp_ket_1'))}", styles['Normal'])],
        [Paragraph("<b>Mediasi 2 (Surat / Tgl / Ket)</b>", styles['Normal']), Paragraph(f"Surat: {format_val(row.get('tp_tgl_surat_2'))} | Tgl: {format_val(row.get('tp_tgl_2'))} | Ket: {format_val(row.get('tp_ket_2'))}", styles['Normal'])],
        [Paragraph("<b>Mediasi 3 (Surat / Tgl / Ket)</b>", styles['Normal']), Paragraph(f"Surat: {format_val(row.get('tp_tgl_surat_3'))} | Tgl: {format_val(row.get('tp_tgl_3'))} | Ket: {format_val(row.get('tp_ket_3'))}", styles['Normal'])],
        [Paragraph("<b>Penyelesaian Akhir / Selesai</b>", styles['Normal']), Paragraph(f"Pilihan: {format_val(row.get('sa_pilihan'))} | Tgl: {format_val(row.get('sa_tanggal'))} | Ket: {format_val(row.get('sa_ket'))}", styles['Normal'])],
        [Paragraph("<b>Catatan Tambahan</b>", styles['Normal']), Paragraph(format_val(row.get('catatan')), styles['Normal'])]
    ]

    t = Table(data_tabel, colWidths=[150, 390])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f3f4f6")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================
# 4. HALAMAN UTAMA: SUMMARY REPORT
# ==========================
st.title("📂 Arsip Rekapitulasi Pengaduan Hubungan Industrial")
st.markdown("---")

df = pd.read_sql_query("SELECT * FROM tabel_pengaduan", conn)

if not df.empty:
    df["tanggal_masuk_dt"] = pd.to_datetime(df["tanggal_masuk"], errors='coerce')
    df["Tahun"] = df["tanggal_masuk_dt"].dt.year.fillna(0).astype(int).astype(str)
    
    bulan_dict = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
        7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    df["Bulan"] = df["tanggal_masuk_dt"].dt.month.map(bulan_dict)

    def tentukan_status_tampil(row):
        if row.get('status') == "Selesai" and row.get('sa_pilihan') and row['sa_pilihan'] != "-":
            return f"Selesai: {row['sa_pilihan']}"
        return row.get('status', '-')
    
    df["Status_Tampil"] = df.apply(tentukan_status_tampil, axis=1)

    # Filter Tahun & Bulan
    col1, col2 = st.columns(2)
    daftar_tahun = sorted(list(df["Tahun"].unique())) if "Tahun" in df.columns else ["2026"]
    tahun_filter = col1.selectbox("Pilih Tahun:", ["Semua Tahun"] + daftar_tahun)
    
    daftar_bulan = ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan_filter = col2.selectbox("Pilih Bulan:", daftar_bulan)

    df_filtered = df.copy()
    if tahun_filter != "Semua Tahun": df_filtered = df_filtered[df_filtered["Tahun"] == tahun_filter]
    if bulan_filter != "Semua Bulan": df_filtered = df_filtered[df_filtered["Bulan"] == bulan_filter]

    # Tombol Export Excel
    col3, col4 = st.columns(2)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtered.drop(columns=['tanggal_masuk_dt', 'Tahun', 'Bulan', 'Status_Tampil'], errors='ignore').to_excel(writer, index=False, sheet_name='Arsip_Pengaduan')
    
    col3.download_button(
        "📥 Export ke Excel", 
        data=output.getvalue(), 
        file_name="Arsip_Pengaduan.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Tabel Utama
    st.dataframe(
        df_filtered,
        column_config={
            "no_urut": "No", "id_pengaduan": "ID", 
            "tanggal_masuk": st.column_config.DateColumn("Tanggal Masuk", format="DD/MM/YYYY"),
            "perihal": "Perihal", "kategori": "Kategori",
            "Status_Tampil": "Status", 
            "sa_tanggal": st.column_config.DateColumn("Tanggal Selesai", format="DD/MM/YYYY"),
            "dok_selesai": st.column_config.LinkColumn("Dokumen Selesai"),
        },
        use_container_width=True, hide_index=True,
        column_order=("no_urut", "id_pengaduan", "tanggal_masuk", "perihal", "kategori", "Status_Tampil", "sa_tanggal", "dok_selesai")
    )

    st.markdown("---")
    st.subheader("🔍 Lihat Detail Lengkap Berdasarkan ID")
    
    list_id = ["-- Pilih ID Pengaduan --"] + df_filtered["id_pengaduan"].tolist()
    pilih_id = st.selectbox("Cari atau Pilih ID Pengaduan:", list_id)

    if pilih_id != "-- Pilih ID Pengaduan --":
        data_detail = df_filtered[df_filtered["id_pengaduan"] == pilih_id].iloc[0]
        
        with st.container():
            st.info(f"✨ **Menampilkan Informasi Rinci untuk ID: {pilih_id}**")
            
            # Tombol Download PDF
            pdf_bytes = generate_pdf(data_detail)
            st.download_button(
                label="📄 Download Laporan PDF",
                data=pdf_bytes,
                file_name=f"Laporan_Pengaduan_{pilih_id}.pdf",
                mime="application/pdf"
            )
            
            # Data Dasar Utama
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Tanggal Masuk:** {data_detail.get('tanggal_masuk', '-')}")
            c2.write(f"**Kategori:** {data_detail.get('kategori', '-')}")
            c3.write(f"**Status Berjalan:** {data_detail.get('status', '-')}")
            
            st.markdown(f"**Perihal:** {data_detail.get('perihal', '-')}")
            
            # Identitas Pihak Terkait
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("##### 👤 Informasi Pelapor")
                st.write(f"**Nama:** {data_detail.get('pelapor', '-')}")
                st.write(f"**Alamat:** {data_detail.get('alamat', '-')}")
                st.write(f"**No. Telp:** {data_detail.get('no_telp', '-')}")
                
            with col_p2:
                st.markdown("##### 🏢 Informasi Terlapor")
                st.write(f"**Nama:** {data_detail.get('terlapor', '-')}")
                st.write(f"**Alamat:** {data_detail.get('alamat_terlapor', '-')}")
                st.write(f"**No. Telp:** {data_detail.get('no_telp_terlapor', '-')}")
            
            st.markdown(f"**Mediator:** {data_detail.get('mediator', '-')}")

            # RIWAYAT & TAHAPAN PENANGANAN
            st.markdown("---")
            st.markdown("##### 📌 Riwayat & Tahapan Penanganan")
            
            st.markdown(f"- **Keterangan Belum Diproses:** {data_detail.get('bd_ket', '-')}")
            st.markdown(f"- **Klarifikasi:** Tgl Surat: {data_detail.get('kl_tgl_surat', '-')} | Tgl Klarifikasi: {data_detail.get('kl_tgl_klarifikasi', '-')} | Ket: {data_detail.get('kl_ket', '-')}")
            st.markdown(f"- **Bipartit:** Tgl Pelaksanaan: {data_detail.get('bp_tgl_pelaksanaan', '-')} | Ket: {data_detail.get('bp_ket', '-')}")
            
            for i in [1, 2, 3]:
                tgl_med = data_detail.get(f'tp_tgl_{i}', '-')
                tgl_surat_med = data_detail.get(f'tp_tgl_surat_{i}', '-')
                ket_med = data_detail.get(f'tp_ket_{i}', '-')
                st.markdown(f"- **Mediasi {i}:** Tgl Surat: {tgl_surat_med} | Tgl Pelaksanaan: {tgl_med} | Ket: {ket_med}")

            # Status Penyelesaian Akhir
            st.markdown("---")
            st.markdown("##### 🏁 Status Akhir / Penyelesaian")
            st.write(f"**Pilihan Penyelesaian:** {data_detail.get('sa_pilihan', '-')}")
            st.write(f"**Tanggal Selesai:** {data_detail.get('sa_tanggal', '-')}")
            st.write(f"**Keterangan Selesai:** {data_detail.get('sa_ket', '-')}")

            # Dokumen & Catatan Tambahan
            st.markdown("---")
            st.markdown("##### 📁 Dokumen & Catatan")
            st.write(f"**Dokumen Laporan:** {data_detail.get('dok_laporan', '-')}")
            st.write(f"**Laporan Selesai:** {data_detail.get('dok_selesai', '-')}")
            st.write(f"**Catatan Tambahan:** {data_detail.get('catatan', '-')}")
else:
    st.info("Belum ada data pengaduan di dalam sistem. Silakan buka menu **Input Data** di samping untuk menambahkan data baru.")
