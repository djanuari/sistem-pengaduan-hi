import datetime
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login.")
  st.stop()

st.set_page_config(
    page_title="Summary Report Pengaduan HI", page_icon="📂", layout="wide"
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()


def format_tanggal_indo(tanggal_str):
  if pd.isna(tanggal_str) or not tanggal_str or str(tanggal_str) == "None" or str(tanggal_str) == "-":
    return "-"
  try:
    dt = datetime.datetime.strptime(str(tanggal_str).split("T")[0], "%Y-%m-%d")
    bulan = [
        "",
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]
    return f"{dt.day} {bulan[dt.month]} {dt.year}"
  except:
    return str(tanggal_str)


st.title("📂 Arsip Rekapitulasi Pengaduan Hubungan Industrial (Cloud)")

# Ambil data dari Supabase
try:
  response = supabase.table("tabel_pengaduan").select("*").execute()
  data = response.data
  df = pd.DataFrame(data)
except Exception as e:
  st.error(f"Gagal mengambil data dari database: {e}")
  df = pd.DataFrame()

if not df.empty:
  # Filter Tahun (Rentang 2033 sampai 2020) & Bulan
  list_tahun = list(range(2033, 2019, -1))
  tahun_opsi = ["Semua Tahun"] + list_tahun
  pilih_tahun = st.selectbox("Pilih Tahun:", tahun_opsi)

  df_filtered = df.copy()
  
  if "tanggal_masuk" in df_filtered.columns:
    df_filtered["tahun"] = pd.to_datetime(
        df_filtered["tanggal_masuk"], errors="coerce"
    ).dt.year
    df_filtered["bulan"] = pd.to_datetime(
        df_filtered["tanggal_masuk"], errors="coerce"
    ).dt.month

    if pilih_tahun != "Semua Tahun":
      df_filtered = df_filtered[df_filtered["tahun"] == int(pilih_tahun)]

    bulan_opsi = {
        "Semua Bulan": None,
        "Januari": 1,
        "Februari": 2,
        "Maret": 3,
        "April": 4,
        "Mei": 5,
        "Juni": 6,
        "Juli": 7,
        "Agustus": 8,
        "September": 9,
        "Oktober": 10,
        "November": 11,
        "Desember": 12,
    }
    pilih_bulan = st.selectbox("Pilih Bulan:", list(bulan_opsi.keys()))
    if pilih_bulan != "Semua Bulan":
      df_filtered = df_filtered[df_filtered["bulan"] == bulan_opsi[pilih_bulan]]

  # ==========================================
  # LOGIKA NOTIFIKASI > 30 HARI KALENDER
  # ==========================================
  if "tanggal_masuk" in df_filtered.columns:
    # Hitung selisih hari dari tanggal masuk ke hari ini (menggunakan UTC/datetime lokal)
    sekarang = pd.Timestamp.now().normalize()
    
    def cek_terlambat(row):
      tgl_masuk = pd.to_datetime(row.get("tanggal_masuk"), errors="coerce")
      status = str(row.get("status", "")).lower()
      
      # Jika belum selesai dan tanggal masuk valid
      if pd.notna(tgl_masuk) and status != "selesai":
        selisih_hari = (sekarang - pd.Timestamp(tgl_masuk).normalize()).days
        if selisih_hari > 30:
          return f"⚠️ Terlambat ({selisih_hari} Hari)"
      return "Normal / Selesai"

    df_filtered["status_waktu"] = df_filtered.apply(cek_terlambat, axis=1)
    
    # Hitung berapa banyak pengaduan yang melebihi 30 hari
    total_terlambat = df_filtered["status_waktu"].str.contains("⚠️").sum()
    if total_terlambat > 0:
      st.error(f"🚨 Perhatian: Ada **{total_terlambat} pengaduan** yang telah melewati rentang waktu 30 hari sejak tanggal masuk dan belum berstatus selesai!")
    else:
      st.success("✅ Semua pengaduan aktif berada dalam batas waktu penanganan (di bawah 30 hari).")

  st.markdown(f"Total Data Ditampilkan: **{len(df_filtered)}** pengaduan")

  # Format Tampilan Tanggal dengan Aman (Mencegah KeyError)
  if "sa_tanggal" in df_filtered.columns:
    df_filtered["sa_tanggal_tampil"] = df_filtered["sa_tanggal"].apply(
        format_tanggal_indo
    )
  else:
    df_filtered["sa_tanggal_tampil"] = "-"

  if "tanggal_masuk" in df_filtered.columns:
    df_filtered["tanggal_masuk_tampil"] = df_filtered["tanggal_masuk"].apply(
        format_tanggal_indo
    )
  else:
    df_filtered["tanggal_masuk_tampil"] = "-"

  # Tombol Export Excel
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Rekap Pengaduan")
  excel_data = output.getvalue()

  st.download_button(
      label="📥 Export ke Excel",
      data=excel_data,
      file_name="Rekap_Pengaduan_HI.xlsx",
      mime=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
  )

  # Tampilkan Data Table
  st.dataframe(df_filtered, use_container_width=True)

else:
  st.info(
      "Belum ada data pengaduan di cloud. Silakan input data terlebih dahulu"
      " melalui menu Input Data."
  )
