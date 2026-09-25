import sqlite3
import pandas as pd
import streamlit as st
import datetime

if not st.session_state.get("logged_in"):
    st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login.")
    st.stop()

st.set_page_config(page_title="Form Input Pengaduan", page_icon="📝", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

st.title("📝 Form Isian Pengaduan HI")

# ==========================================
# VARIABEL OPSI (WAJIB ADA DI SINI)
# ==========================================
kategori_opsi = [
    "Perselisihan Hak", "Perselisihan Kepentingan", 
    "Perselisihan Pemutusan Hubungan Kerja (PHK)", 
    "Perselisihan Antar Serikat Pekerja", "Lainnya"
]
status_opsi = ["Belum diproses", "Klarifikasi", "Bipartit", "Tripartit", "Selesai"]
pilihan_selesai_opsi = ["-", "Perjanjian Bersama (PB)", "Anjuran Tertulis", "Gugatan Hukum ke Pengadilan Hubungan Industrial (PHI)"]

# Membuat 3 Tab Halaman
tab1, tab2, tab3 = st.tabs(["➕ Input Data Baru", "✏️ Update / Edit Data", "🗑️ Hapus Data"])

# Helper function untuk mengubah tanggal ke string
def f_date(d): return str(d) if d else "-"

# ==========================================
# TAB 1: INPUT DATA BARU
# ==========================================
with tab1:
    with st.form("form_tambah_baru", clear_on_submit=True):
        st.subheader("Data Dasar Pengaduan")
        c1, c2 = st.columns(2)
        id_pengaduan = c1.text_input("ID Pengaduan")
        tanggal_masuk = c2.date_input("Tanggal Masuk", format="DD/MM/YYYY")
        
        perihal = st.text_area("Perihal")
        kategori = st.selectbox("Kategori", kategori_opsi)
        
        c3, c4 = st.columns(2)
        pelapor = c3.text_input("Pelapor")
        terlapor = c4.text_input("Terlapor")
        
        st.markdown("---")
        st.subheader("Status Penanganan")
        status = st.selectbox("Status Berjalan", status_opsi)
        
        bd_ket = st.text_area("Keterangan (Belum diproses)")
        
        st.markdown("**Data Klarifikasi**")
        kl1, kl2 = st.columns(2)
        kl_tgl_surat = kl1.date_input("Tanggal Surat Undangan (Klarifikasi)", value=None, format="DD/MM/YYYY")
        kl_tgl_klarifikasi = kl2.date_input("Tanggal Klarifikasi", value=None, format="DD/MM/YYYY")
        kl_ket = st.text_area("Keterangan (Klarifikasi)")
        
        st.markdown("**Data Bipartit**")
        bp_tgl_pelaksanaan = st.date_input("Tanggal Pelaksanaan (Bipartit)", value=None, format="DD/MM/YYYY")
        bp_ket = st.text_area("Keterangan (Bipartit)")
        
        st.markdown("**Data Tripartit (Mediasi 1)**")
        tp1, tp2 = st.columns(2)
        tp_tgl_surat_1 = tp1.date_input("Tgl Surat Med 1", value=None, format="DD/MM/YYYY")
        tp_tgl_1 = tp2.date_input("Tgl Pelaksanaan Med 1", value=None, format="DD/MM/YYYY")
        tp_ket_1 = st.text_area("Keterangan Med 1")
        
        st.markdown("**Data Tripartit (Mediasi 2)**")
        tp4, tp5 = st.columns(2)
        tp_tgl_surat_2 = tp4.date_input("Tgl Surat Med 2", value=None, format="DD/MM/YYYY")
        tp_tgl_2 = tp5.date_input("Tgl Pelaksanaan Med 2", value=None, format="DD/MM/YYYY")
        tp_ket_2 = st.text_area("Keterangan Med 2")
        
        st.markdown("**Data Tripartit (Mediasi 3)**")
        tp7, tp8 = st.columns(2)
        tp_tgl_surat_3 = tp7.date_input("Tgl Surat Med 3", value=None, format="DD/MM/YYYY")
        tp_tgl_3 = tp8.date_input("Tgl Pelaksanaan Med 3", value=None, format="DD/MM/YYYY")
        tp_ket_3 = st.text_area("Keterangan Med 3")
        
        st.markdown("---")
        st.subheader("Status Akhir (Jika Selesai)")
        sa1, sa2 = st.columns(2)
        sa_tanggal = sa1.date_input("Tanggal Selesai", value=None, format="DD/MM/YYYY")
        sa_pilihan = sa2.selectbox("Pilihan Penyelesaian", pilihan_selesai_opsi)
        sa_ket = st.text_area("Keterangan Status Selesai")

        st.markdown("---")
        st.subheader("Dokumen & Catatan")
        d1, d2 = st.columns(2)
        dok_laporan = d1.text_input("Link Unggah Dokumen Laporan")
        dok_selesai = d2.text_input("Link Unggah Laporan Selesai")
        catatan = st.text_area("Catatan Tambahan")
        
        submit_baru = st.form_submit_button("Simpan Data Baru")

    if submit_baru:
        if id_pengaduan.strip() == "":
            st.error("ID Pengaduan wajib diisi!")
        else:
            try:
                cursor.execute("""
                INSERT INTO tabel_pengaduan (
                    id_pengaduan, tanggal_masuk, perihal, kategori, pelapor, terlapor, status, bd_ket,
                    kl_tgl_surat, kl_tgl_klarifikasi, kl_ket, bp_tgl_pelaksanaan, bp_ket,
                    tp_tgl_surat_1, tp_tgl_1, tp_ket_1, tp_tgl_surat_2, tp_tgl_2, tp_ket_2, tp_tgl_surat_3, tp_tgl_3, tp_ket_3,
                    sa_tanggal, sa_pilihan, sa_ket, dok_laporan, dok_selesai, catatan
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    id_pengaduan, f_date(tanggal_masuk), perihal, kategori, pelapor, terlapor, status, bd_ket,
                    f_date(kl_tgl_surat), f_date(kl_tgl_klarifikasi), kl_ket, f_date(bp_tgl_pelaksanaan), bp_ket,
                    f_date(tp_tgl_surat_1), f_date(tp_tgl_1), tp_ket_1, f_date(tp_tgl_surat_2), f_date(tp_tgl_2), tp_ket_2, f_date(tp_tgl_surat_3), f_date(tp_tgl_3), tp_ket_3,
                    f_date(sa_tanggal), sa_pilihan, sa_ket, dok_laporan, dok_selesai, catatan
                ))
                conn.commit()
                st.success(f"Berhasil! Data {id_pengaduan} disimpan.")
            except sqlite3.IntegrityError:
                st.error("Gagal: ID Pengaduan sudah ada! Gunakan tab Edit jika ingin memperbarui.")

# ==========================================
# TAB 2: EDIT DATA SECARA KESELURUHAN
# ==========================================
with tab2:
    df_edit = pd.read_sql_query("SELECT id_pengaduan FROM tabel_pengaduan", conn)
    if not df_edit.empty:
        id_pilihan = st.selectbox("Pilih ID Pengaduan yang ingin diedit:", df_edit["id_pengaduan"].tolist())
        df_row = pd.read_sql_query(f"SELECT * FROM tabel_pengaduan WHERE id_pengaduan = '{id_pilihan}'", conn).iloc[0]
        
        # Helper fungsi untuk konversi nilai database kembali ke form
        def str_to_date(date_str):
            if pd.isna(date_str) or date_str == "-" or not date_str: return None
            try: return datetime.datetime.strptime(str(date_str), "%Y-%m-%d").date()
            except: return None
            
        def safe_str(val): return str(val) if val and str(val) != "None" else ""

        with st.form("form_update_keseluruhan"):
            st.info(f"Mengedit Keseluruhan Data untuk ID: **{id_pilihan}**")
            
            st.subheader("Data Dasar Pengaduan")
            e_c1, e_c2 = st.columns(2)
            u_id = e_c1.text_input("ID Pengaduan (Tidak bisa diubah)", value=df_row['id_pengaduan'], disabled=True)
            u_tanggal_masuk = e_c2.date_input("Tanggal Masuk", value=str_to_date(df_row['tanggal_masuk']), key="e_tgl", format="DD/MM/YYYY")
            
            u_perihal = st.text_area("Perihal", value=safe_str(df_row['perihal']), key="e_perihal")
            
            kat_idx = kategori_opsi.index(df_row['kategori']) if df_row['kategori'] in kategori_opsi else 0
            u_kategori = st.selectbox("Kategori", kategori_opsi, index=kat_idx, key="e_kat")
            
            e_c3, e_c4 = st.columns(2)
            u_pelapor = e_c3.text_input("Pelapor", value=safe_str(df_row['pelapor']), key="e_pel")
            u_terlapor = e_c4.text_input("Terlapor", value=safe_str(df_row['terlapor']), key="e_ter")
            
            st.markdown("---")
            st.subheader("Status Penanganan")
            stat_idx = status_opsi.index(df_row['status']) if df_row['status'] in status_opsi else 0
            u_status = st.selectbox("Status Berjalan", status_opsi, index=stat_idx, key="e_stat")
            
            u_bd_ket = st.text_area("Keterangan (Belum diproses)", value=safe_str(df_row['bd_ket']), key="e_bd_ket")
            
            st.markdown("**Data Klarifikasi**")
            e_kl1, e_kl2 = st.columns(2)
            u_kl_tgl_surat = e_kl1.date_input("Tanggal Surat Undangan (Klarifikasi)", value=str_to_date(df_row['kl_tgl_surat']), key="e_kl1", format="DD/MM/YYYY")
            u_kl_tgl_klarifikasi = e_kl2.date_input("Tanggal Klarifikasi", value=str_to_date(df_row['kl_tgl_klarifikasi']), key="e_kl2", format="DD/MM/YYYY")
            u_kl_ket = st.text_area("Keterangan (Klarifikasi)", value=safe_str(df_row['kl_ket']), key="e_kl_ket")
            
            st.markdown("**Data Bipartit**")
            u_bp_tgl_pelaksanaan = st.date_input("Tanggal Pelaksanaan (Bipartit)", value=str_to_date(df_row['bp_tgl_pelaksanaan']), key="e_bp1", format="DD/MM/YYYY")
            u_bp_ket = st.text_area("Keterangan (Bipartit)", value=safe_str(df_row['bp_ket']), key="e_bp_ket")
            
            st.markdown("**Data Tripartit (Mediasi 1)**")
            e_tp1, e_tp2 = st.columns(2)
            u_tp_tgl_surat_1 = e_tp1.date_input("Tgl Surat Med 1", value=str_to_date(df_row['tp_tgl_surat_1']), key="e_tp1", format="DD/MM/YYYY")
            u_tp_tgl_1 = e_tp2.date_input("Tgl Pelaksanaan Med 1", value=str_to_date(df_row['tp_tgl_1']), key="e_tp2", format="DD/MM/YYYY")
            u_tp_ket_1 = st.text_area("Keterangan Med 1", value=safe_str(df_row['tp_ket_1']), key="e_tp_ket1")
            
            st.markdown("**Data Tripartit (Mediasi 2)**")
            e_tp4, e_tp5 = st.columns(2)
            u_tp_tgl_surat_2 = e_tp4.date_input("Tgl Surat Med 2", value=str_to_date(df_row['tp_tgl_surat_2']), key="e_tp4", format="DD/MM/YYYY")
            u_tp_tgl_2 = e_tp5.date_input("Tgl Pelaksanaan Med 2", value=str_to_date(df_row['tp_tgl_2']), key="e_tp5", format="DD/MM/YYYY")
            u_tp_ket_2 = st.text_area("Keterangan Med 2", value=safe_str(df_row['tp_ket_2']), key="e_tp_ket2")
            
            st.markdown("**Data Tripartit (Mediasi 3)**")
            e_tp7, e_tp8 = st.columns(2)
            u_tp_tgl_surat_3 = e_tp7.date_input("Tgl Surat Med 3", value=str_to_date(df_row['tp_tgl_surat_3']), key="e_tp7", format="DD/MM/YYYY")
            u_tp_tgl_3 = e_tp8.date_input("Tgl Pelaksanaan Med 3", value=str_to_date(df_row['tp_tgl_3']), key="e_tp8", format="DD/MM/YYYY")
            u_tp_ket_3 = st.text_area("Keterangan Med 3", value=safe_str(df_row['tp_ket_3']), key="e_tp_ket3")
            
            st.markdown("---")
            st.subheader("Status Akhir (Jika Selesai)")
            e_sa1, e_sa2 = st.columns(2)
            u_sa_tanggal = e_sa1.date_input("Tanggal Selesai", value=str_to_date(df_row['sa_tanggal']), key="e_sa1", format="DD/MM/YYYY")
            
            sa_idx = pilihan_selesai_opsi.index(df_row['sa_pilihan']) if df_row['sa_pilihan'] in pilihan_selesai_opsi else 0
            u_sa_pilihan = e_sa2.selectbox("Pilihan Penyelesaian", pilihan_selesai_opsi, index=sa_idx, key="e_sa2")
            u_sa_ket = st.text_area("Keterangan Status Selesai", value=safe_str(df_row['sa_ket']), key="e_sa_ket")

            st.markdown("---")
            st.subheader("Dokumen & Catatan")
            e_d1, e_d2 = st.columns(2)
            u_dok_laporan = e_d1.text_input("Link Unggah Dokumen Laporan", value=safe_str(df_row['dok_laporan']), key="e_d1")
            u_dok_selesai = e_d2.text_input("Link Unggah Laporan Selesai", value=safe_str(df_row['dok_selesai']), key="e_d2")
            u_catatan = st.text_area("Catatan Tambahan", value=safe_str(df_row['catatan']), key="e_catatan")
            
            submit_update = st.form_submit_button("Simpan Perubahan Data")
            
            if submit_update:
                cursor.execute("""
                    UPDATE tabel_pengaduan 
                    SET tanggal_masuk=?, perihal=?, kategori=?, pelapor=?, terlapor=?, status=?, bd_ket=?,
                        kl_tgl_surat=?, kl_tgl_klarifikasi=?, kl_ket=?, bp_tgl_pelaksanaan=?, bp_ket=?,
                        tp_tgl_surat_1=?, tp_tgl_1=?, tp_ket_1=?, tp_tgl_surat_2=?, tp_tgl_2=?, tp_ket_2=?, tp_tgl_surat_3=?, tp_tgl_3=?, tp_ket_3=?,
                        sa_tanggal=?, sa_pilihan=?, sa_ket=?, dok_laporan=?, dok_selesai=?, catatan=?
                    WHERE id_pengaduan=?
                """, (
                    f_date(u_tanggal_masuk), u_perihal, u_kategori, u_pelapor, u_terlapor, u_status, u_bd_ket,
                    f_date(u_kl_tgl_surat), f_date(u_kl_tgl_klarifikasi), u_kl_ket, f_date(u_bp_tgl_pelaksanaan), u_bp_ket,
                    f_date(u_tp_tgl_surat_1), f_date(u_tp_tgl_1), u_tp_ket_1, f_date(u_tp_tgl_surat_2), f_date(u_tp_tgl_2), u_tp_ket_2, f_date(u_tp_tgl_surat_3), f_date(u_tp_tgl_3), u_tp_ket_3,
                    f_date(u_sa_tanggal), u_sa_pilihan, u_sa_ket, u_dok_laporan, u_dok_selesai, u_catatan,
                    id_pilihan
                ))
                conn.commit()
                st.success(f"Data {id_pilihan} berhasil diperbarui secara menyeluruh!")
    else:
        st.write("Belum ada data untuk diedit.")

# ==========================================
# TAB 3: HAPUS DATA
# ==========================================
with tab3:
    if not df_edit.empty:
        id_hapus = st.selectbox("Pilih ID untuk DIHAPUS:", df_edit["id_pengaduan"].tolist(), key="hapus_id")
        if st.button("🗑️ Hapus Permanen"):
            cursor.execute("DELETE FROM tabel_pengaduan WHERE id_pengaduan = ?", (id_hapus,))
            conn.commit()
            st.success(f"Data {id_hapus} berhasil dihapus!")
            st.rerun()