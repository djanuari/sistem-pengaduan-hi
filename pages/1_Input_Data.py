import datetime
import pandas as pd
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login.")
  st.stop()

st.set_page_config(
    page_title="Form Input & Edit Pengaduan", page_icon="📝", layout="wide"
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("📝 Form Isian & Pengelolaan Pengaduan HI (Cloud Database)")

kategori_opsi = [
    "Perselisihan Hak",
    "Perselisihan Kepentingan",
    "Perselisihan Pemutusan Hubungan Kerja (PHK)",
    "Perselisihan Antar Serikat Pekerja",
    "Lainnya",
]
status_opsi = ["Belum diproses", "Klarifikasi", "Bipartit", "Tripartit", "Selesai"]

pilihan_selesai_opsi = [
    "-",
    "Perjanjian Bersama (PB)",
    "Anjuran Tertulis",
    "Laporan Dibatalkan / Pencabutan Laporan",
]

tab1, tab2, tab3 = st.tabs(
    ["➕ Input Data Baru", "✏️ Update / Edit Data", "🗑️ Hapus Data"]
)


def f_date(d):
  return str(d) if d else None


def str_to_date(date_str):
  if pd.isna(date_str) or date_str == "-" or not date_str or date_str == "None":
    return None
  try:
    return datetime.datetime.strptime(str(date_str).split("T")[0], "%Y-%m-%d").date()
  except:
    return None


def safe_str(val):
  return str(val) if val and str(val) != "None" else ""


# ==========================================
# TAB 1: INPUT DATA BARU
# ==========================================
with tab1:
  st.subheader("Tambah Data Pengaduan Baru")
  with st.form("form_tambah_baru", clear_on_submit=True):
    c1, c2 = st.columns(2)
    id_pengaduan = c1.text_input("ID Pengaduan")
    tanggal_masuk = c2.date_input("Tanggal Masuk")

    perihal = st.text_area("Perihal")
    kategori = st.selectbox("Kategori", kategori_opsi)

    st.markdown("**Informasi Pelapor**")
    c3, c4 = st.columns(2)
    pelapor = c3.text_input("Pelapor / Pemohon")
    nik_pelapor = c4.text_input("NIK Pelapor")

    c5, c6 = st.columns(2)
    alamat = c5.text_area("Alamat Pelapor")
    no_telp = c6.text_input("Nomor Telepon / Kontak Pelapor")

    st.markdown("**Informasi Terlapor / Perusahaan**")
    t1, t2 = st.columns(2)
    terlapor = t1.text_input("Terlapor / Perusahaan")
    email_terlapor = t2.text_input("Email Perusahaan Terlapor")

    t3, t4 = st.columns(2)
    nib_terlapor = t3.text_input("NIB Terlapor")
    jenis_usaha_terlapor = t4.text_input("Jenis Usaha Terlapor")

    c7, c8 = st.columns(2)
    alamat_terlapor = c7.text_area("Alamat Terlapor")
    no_telp_terlapor = c8.text_input("No. Telepon Terlapor")

    mediator = st.text_input("Mediator")

    st.markdown("---")
    st.subheader("Status Penanganan")
    status = st.selectbox("Status Berjalan", status_opsi)
    bd_ket = st.text_area("Keterangan (Belum diproses)")

    st.markdown("**Data Klarifikasi**")
    kl1, kl2 = st.columns(2)
    kl_tgl_surat = kl1.date_input("Tanggal Surat Undangan (Klarifikasi)", value=None)
    kl_tgl_klarifikasi = kl2.date_input("Tanggal Klarifikasi", value=None)
    kl_ket = st.text_area("Keterangan (Klarifikasi)")

    st.markdown("**Data Bipartit**")
    bp_tgl_pelaksanaan = st.date_input(
        "Tanggal Pelaksanaan (Bipartit)", value=None
    )
    bp_ket = st.text_area("Keterangan (Bipartit)")

    st.markdown("**Data Tripartit (Mediasi 1)**")
    tp1, tp2 = st.columns(2)
    tp_tgl_surat_1 = tp1.date_input("Tgl Surat Med 1", value=None)
    tp_tgl_1 = tp2.date_input("Tgl Pelaksanaan Med 1", value=None)
    tp_ket_1 = st.text_area("Keterangan Med 1")

    st.markdown("**Data Tripartit (Mediasi 2)**")
    tp4, tp5 = st.columns(2)
    tp_tgl_surat_2 = tp4.date_input("Tgl Surat Med 2", value=None)
    tp_tgl_2 = tp5.date_input("Tgl Pelaksanaan Med 2", value=None)
    tp_ket_2 = st.text_area("Keterangan Med 2")

    st.markdown("**Data Tripartit (Mediasi 3)**")
    tp7, tp8 = st.columns(2)
    tp_tgl_surat_3 = tp7.date_input("Tgl Surat Med 3", value=None)
    tp_tgl_3 = tp8.date_input("Tgl Pelaksanaan Med 3", value=None)
    tp_ket_3 = st.text_area("Keterangan Med 3")

    st.markdown("---")
    st.subheader("Status Akhir (Jika Selesai)")
    sa1, sa2 = st.columns(2)
    sa_tanggal = sa1.date_input("Tanggal Selesai", value=None)
    sa_pilihan = sa2.selectbox("Pilihan Penyelesaian", pilihan_selesai_opsi)
    sa_ket = st.text_area("Keterangan Status Selesai")

    st.markdown("---")
    st.subheader("Dokumen & Catatan")
    d1, d2 = st.columns(2)
    dok_laporan = d1.text_input("Link Unggah Dokumen Laporan")
    dok_selesai = d2.text_input("Link Unggah Laporan Selesai")
    catatan = st.text_area("Catatan Tambahan")

    submit_baru = st.form_submit_button("Simpan Data Baru ke Cloud")

  if submit_baru:
    if id_pengaduan.strip() == "":
      st.error("ID Pengaduan wajib diisi!")
    else:
      try:
        data_baru = {
            "id_pengaduan": id_pengaduan.strip(),
            "tanggal_masuk": f_date(tanggal_masuk),
            "perihal": perihal,
            "kategori": kategori,
            "pelapor": pelapor,
            "nik_pelapor": nik_pelapor,
            "terlapor": terlapor,
            "email_terlapor": email_terlapor,
            "nib_terlapor": nib_terlapor,
            "jenis_usaha_terlapor": jenis_usaha_terlapor,
            "alamat": alamat,
            "no_telp": no_telp,
            "alamat_terlapor": alamat_terlapor,
            "no_telp_terlapor": no_telp_terlapor,
            "mediator": mediator,
            "status": status,
            "bd_ket": bd_ket,
            "kl_tgl_surat": f_date(kl_tgl_surat),
            "kl_tgl_klarifikasi": f_date(kl_tgl_klarifikasi),
            "kl_ket": kl_ket,
            "bp_tgl_pelaksanaan": f_date(bp_tgl_pelaksanaan),
            "bp_ket": bp_ket,
            "tp_tgl_surat_1": f_date(tp_tgl_surat_1),
            "tp_tgl_1": f_date(tp_tgl_1),
            "tp_ket_1": tp_ket_1,
            "tp_tgl_surat_2": f_date(tp_tgl_surat_2),
            "tp_tgl_2": f_date(tp_tgl_2),
            "tp_ket_2": tp_ket_2,
            "tp_tgl_surat_3": f_date(tp_tgl_surat_3),
            "tp_tgl_3": f_date(tp_tgl_3),
            "tp_ket_3": tp_ket_3,
            "sa_tanggal": f_date(sa_tanggal),
            "sa_pilihan": sa_pilihan,
            "sa_ket": sa_ket,
            "dok_laporan": dok_laporan,
            "dok_selesai": dok_selesai,
            "catatan": catatan,
        }
        supabase.table("tabel_pengaduan").insert(data_baru).execute()
        st.success(
            f"Berhasil! Data {id_pengaduan} disimpan secara permanen di cloud."
        )
      except Exception as e:
        st.error(
            f"Gagal menyimpan. Pastikan ID Pengaduan belum terdaftar: {e}"
        )

# ==========================================
# TAB 2: EDIT DATA SECARA KESELURUHAN
# ==========================================
with tab2:
  try:
    res = (
        supabase.table("tabel_pengaduan").select("id_pengaduan").execute()
    )
    df_edit = pd.DataFrame(res.data)
  except Exception:
    df_edit = pd.DataFrame()

  if not df_edit.empty and "id_pengaduan" in df_edit.columns:
    id_pilihan = st.selectbox(
        "Pilih ID Pengaduan yang ingin diedit:",
        df_edit["id_pengaduan"].tolist(),
        key="select_edit_id_unik",
    )

    try:
      res_row = (
          supabase.table("tabel_pengaduan")
          .select("*")
          .eq("id_pengaduan", id_pilihan)
          .execute()
      )
      df_row_result = pd.DataFrame(res_row.data)
    except Exception:
      df_row_result = pd.DataFrame()

    if not df_row_result.empty:
      df_row = df_row_result.iloc[0]

      st.info(f"Mengedit Keseluruhan Data untuk ID: **{id_pilihan}**")

      st.subheader("Data Dasar Pengaduan")
      e_c1, e_c2 = st.columns(2)
      e_c1.text_input(
          "ID Pengaduan (Tidak bisa diubah)",
          value=df_row["id_pengaduan"],
          disabled=True,
          key=f"u_id_{id_pilihan}",
      )
      u_tanggal_masuk = e_c2.date_input(
          "Tanggal Masuk",
          value=str_to_date(df_row["tanggal_masuk"]),
          key=f"u_tgl_{id_pilihan}",
      )

      u_perihal = st.text_area(
          "Perihal",
          value=safe_str(df_row["perihal"]),
          key=f"u_perihal_{id_pilihan}",
      )

      kat_idx = (
          kategori_opsi.index(df_row["kategori"])
          if df_row["kategori"] in kategori_opsi
          else 0
      )
      u_kategori = st.selectbox(
          "Kategori",
          kategori_opsi,
          index=kat_idx,
          key=f"u_kat_{id_pilihan}",
      )

      st.markdown("**Informasi Pelapor**")
      e_c3, e_c4 = st.columns(2)
      u_pelapor = e_c3.text_input(
          "Pelapor / Pemohon",
          value=safe_str(df_row["pelapor"]),
          key=f"u_pel_{id_pilihan}",
      )
      u_nik_pelapor = e_c4.text_input(
          "NIK Pelapor",
          value=safe_str(df_row.get("nik_pelapor", "")),
          key=f"u_nik_{id_pilihan}",
      )

      e_c5, e_c6 = st.columns(2)
      u_alamat = e_c5.text_area(
          "Alamat Pelapor",
          value=safe_str(df_row.get("alamat", "")),
          key=f"u_alamat_{id_pilihan}",
      )
      u_no_telp = e_c6.text_input(
          "Nomor Telepon / Kontak Pelapor",
          value=safe_str(df_row.get("no_telp", "")),
          key=f"u_notelp_{id_pilihan}",
      )

      st.markdown("**Informasi Terlapor / Perusahaan**")
      u_t1, u_t2 = st.columns(2)
      u_terlapor = u_t1.text_input(
          "Terlapor / Perusahaan",
          value=safe_str(df_row["terlapor"]),
          key=f"u_ter_{id_pilihan}",
      )
      u_email_terlapor = u_t2.text_input(
          "Email Perusahaan Terlapor",
          value=safe_str(df_row.get("email_terlapor", "")),
          key=f"u_email_{id_pilihan}",
      )

      u_t3, u_t4 = st.columns(2)
      u_nib_terlapor = u_t3.text_input(
          "NIB Terlapor",
          value=safe_str(df_row.get("nib_terlapor", "")),
          key=f"u_nib_{id_pilihan}",
      )
      u_jenis_usaha_terlapor = u_t4.text_input(
          "Jenis Usaha Terlapor",
          value=safe_str(df_row.get("jenis_usaha_terlapor", "")),
          key=f"u_jenis_{id_pilihan}",
      )

      e_c7, e_c8 = st.columns(2)
      u_alamat_terlapor = e_c7.text_area(
          "Alamat Terlapor",
          value=safe_str(df_row.get("alamat_terlapor", "")),
          key=f"u_alamatterlapor_{id_pilihan}",
      )
      u_no_telp_terlapor = e_c8.text_input(
          "No. Telepon Terlapor",
          value=safe_str(df_row.get("no_telp_terlapor", "")),
          key=f"u_notelpterlapor_{id_pilihan}",
      )

      u_mediator = st.text_input(
          "Mediator",
          value=safe_str(df_row.get("mediator", "")),
          key=f"u_mediator_{id_pilihan}",
      )

      st.markdown("---")
      st.subheader("Status Penanganan")
      stat_idx = (
          status_opsi.index(df_row["status"])
          if df_row["status"] in status_opsi
          else 0
      )
      u_status = st.selectbox(
          "Status Berjalan",
          status_opsi,
          index=stat_idx,
          key=f"u_stat_{id_pilihan}",
      )
      u_bd_ket = st.text_area(
          "Keterangan (Belum diproses)",
          value=safe_str(df_row["bd_ket"]),
          key=f"u_bd_ket_{id_pilihan}",
      )

      st.markdown("**Data Klarifikasi**")
      e_kl1, e_kl2 = st.columns(2)
      u_kl_tgl_surat = e_kl1.date_input(
          "Tanggal Surat Undangan (Klarifikasi)",
          value=str_to_date(df_row["kl_tgl_surat"]),
          key=f"u_kl1_{id_pilihan}",
      )
      u_kl_tgl_klarifikasi = e_kl2.date_input(
          "Tanggal Klarifikasi",
          value=str_to_date(df_row["kl_tgl_klarifikasi"]),
          key=f"u_kl2_{id_pilihan}",
      )
      u_kl_ket = st.text_area(
          "Keterangan (Klarifikasi)",
          value=safe_str(df_row["kl_ket"]),
          key=f"u_kl_ket_{id_pilihan}",
      )

      st.markdown("**Data Bipartit**")
      u_bp_tgl_pelaksanaan = st.date_input(
          "Tanggal Pelaksanaan (Bipartit)",
          value=str_to_date(df_row["bp_tgl_pelaksanaan"]),
          key=f"u_bp1_{id_pilihan}",
      )
      u_bp_ket = st.text_area(
          "Keterangan (Bipartit)",
          value=safe_str(df_row["bp_ket"]),
          key=f"u_bp_ket_{id_pilihan}",
      )

      st.markdown("**Data Tripartit (Mediasi 1)**")
      e_tp1, e_tp2 = st.columns(2)
      u_tp_tgl_surat_1 = e_tp1.date_input(
          "Tgl Surat Med 1",
          value=str_to_date(df_row["tp_tgl_surat_1"]),
          key=f"u_tp1_{id_pilihan}",
      )
      u_tp_tgl_1 = e_tp2.date_input(
          "Tgl Pelaksanaan Med 1",
          value=str_to_date(df_row["tp_tgl_1"]),
          key=f"u_tp2_{id_pilihan}",
      )
      u_tp_ket_1 = st.text_area(
          "Keterangan Med 1",
          value=safe_str(df_row["tp_ket_1"]),
          key=f"u_tp_ket1_{id_pilihan}",
      )

      st.markdown("**Data Tripartit (Mediasi 2)**")
      e_tp4, e_tp5 = st.columns(2)
      u_tp_tgl_surat_2 = e_tp4.date_input(
          "Tgl Surat Med 2",
          value=str_to_date(df_row["tp_tgl_surat_2"]),
          key=f"u_tp4_{id_pilihan}",
      )
      u_tp_tgl_2 = e_tp5.date_input(
          "Tgl Pelaksanaan Med 2",
          value=str_to_date(df_row["tp_tgl_2"]),
          key=f"u_tp5_{id_pilihan}",
      )
      u_tp_ket_2 = st.text_area(
          "Keterangan Med 2",
          value=safe_str(df_row["tp_ket_2"]),
          key=f"u_tp_ket2_{id_pilihan}",
      )

      st.markdown("**Data Tripartit (Mediasi 3)**")
      e_tp7, e_tp8 = st.columns(2)
      u_tp_tgl_surat_3 = e_tp7.date_input(
          "Tgl Surat Med 3",
          value=str_to_date(df_row["tp_tgl_surat_3"]),
          key=f"u_tp7_{id_pilihan}",
      )
      u_tp_tgl_3 = e_tp8.date_input(
          "Tgl Pelaksanaan Med 3",
          value=str_to_date(df_row["tp_tgl_3"]),
          key=f"u_tp8_{id_pilihan}",
      )
      u_tp_ket_3 = st.text_area(
          "Keterangan Med 3",
          value=safe_str(df_row["tp_ket_3"]),
          key=f"u_tp_ket3_{id_pilihan}",
      )

      st.markdown("---")
      st.subheader("Status Akhir (Jika Selesai)")
      e_sa1, e_sa2 = st.columns(2)
      u_sa_tanggal = e_sa1.date_input(
          "Tanggal Selesai",
          value=str_to_date(df_row["sa_tanggal"]),
          key=f"u_sa1_{id_pilihan}",
      )

      sa_idx = (
          pilihan_selesai_opsi.index(df_row["sa_pilihan"])
          if df_row["sa_pilihan"] in pilihan_selesai_opsi
          else 0
      )
      u_sa_pilihan = e_sa2.selectbox(
          "Pilihan Penyelesaian",
          pilihan_selesai_opsi,
          index=sa_idx,
          key=f"u_sa2_{id_pilihan}",
      )
      u_sa_ket = st.text_area(
          "Keterangan Status Selesai",
          value=safe_str(df_row["sa_ket"]),
          key=f"u_sa_ket_{id_pilihan}",
      )

      st.markdown("---")
      st.subheader("Dokumen & Catatan")
      e_d1, e_d2 = st.columns(2)
      u_dok_laporan = e_d1.text_input(
          "Link Unggah Dokumen Laporan",
          value=safe_str(df_row["dok_laporan"]),
          key=f"u_d1_{id_pilihan}",
      )
      u_dok_selesai = e_d2.text_input(
          "Link Unggah Laporan Selesai",
          value=safe_str(df_row["dok_selesai"]),
          key=f"u_d2_{id_pilihan}",
      )
      u_catatan = st.text_area(
          "Catatan Tambahan",
          value=safe_str(df_row["catatan"]),
          key=f"u_cat_{id_pilihan}",
      )

      if st.button("Simpan Perubahan Data", type="primary"):
        try:
          data_update = {
              "tanggal_masuk": f_date(u_tanggal_masuk),
              "perihal": u_perihal,
              "kategori": u_kategori,
              "pelapor": u_pelapor,
              "nik_pelapor": u_nik_pelapor,
              "terlapor": u_terlapor,
              "email_terlapor": u_email_terlapor,
              "nib_terlapor": u_nib_terlapor,
              "jenis_usaha_terlapor": u_jenis_usaha_terlapor,
              "alamat": u_alamat,
              "no_telp": u_no_telp,
              "alamat_terlapor": u_alamat_terlapor,
              "no_telp_terlapor": u_no_telp_terlapor,
              "mediator": u_mediator,
              "status": u_status,
              "bd_ket": u_bd_ket,
              "kl_tgl_surat": f_date(u_kl_tgl_surat),
              "kl_tgl_klarifikasi": f_date(u_kl_tgl_klarifikasi),
              "kl_ket": u_kl_ket,
              "bp_tgl_pelaksanaan": f_date(u_bp_tgl_pelaksanaan),
              "bp_ket": u_bp_ket,
              "tp_tgl_surat_1": f_date(u_tp_tgl_surat_1),
              "tp_tgl_1": f_date(u_tp_tgl_1),
              "tp_ket_1": u_tp_ket_1,
              "tp_tgl_surat_2": f_date(u_tp_tgl_surat_2),
              "tp_tgl_2": f_date(u_tp_tgl_2),
              "tp_ket_2": u_tp_ket_2,
              "tp_tgl_surat_3": f_date(u_tp_tgl_surat_3),
              "tp_tgl_3": f_date(u_tp_tgl_3),
              "tp_ket_3": u_tp_ket_3,
              "sa_tanggal": f_date(u_sa_tanggal),
              "sa_pilihan": u_sa_pilihan,
              "sa_ket": u_sa_ket,
              "dok_laporan": u_dok_laporan,
              "dok_selesai": u_dok_selesai,
              "catatan": u_catatan,
          }
          supabase.table("tabel_pengaduan").update(data_update).eq(
              "id_pengaduan", id_pilihan
          ).execute()
          st.success(f"Data {id_pilihan} berhasil diperbarui di cloud!")
        except Exception as e:
          st.error(f"Gagal memperbarui data: {e}")
  else:
    st.write("Belum ada data untuk diedit.")

# ==========================================
# TAB 3: HAPUS DATA
# ==========================================
with tab3:
  if not df_edit.empty and "id_pengaduan" in df_edit.columns:
    id_hapus = st.selectbox(
        "Pilih ID untuk DIHAPUS:",
        df_edit["id_pengaduan"].tolist(),
        key="hapus_id_unik",
    )
    if st.button("🗑️ Hapus Permanen", type="secondary"):
      try:
        supabase.table("tabel_pengaduan").delete().eq(
            "id_pengaduan", id_hapus
        ).execute()
        st.success(f"Data {id_hapus} berhasil dihapus dari cloud!")
        st.rerun()
      except Exception as e:
        st.error(f"Gagal menghapus data: {e}")
  else:
    st.write("Tidak ada data untuk dihapus.")
