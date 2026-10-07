from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Silakan login terlebih dahulu.")
  st.stop()

st.title("📊 Monitoring Kepesertaan Berdasarkan Jenjang Pendidikan")
st.write(
    "Rekapitulasi jumlah satuan pendidikan, PTK, serta rincian daftar sekolah."
)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# Daftar Jenjang Pendidikan Resmi
list_jenjang = [
    "PAUD",
    "Kelompok Bermain (KB)",
    "Taman Kanak-Kanak (TK)",
    "Sekolah Dasar (SD)",
    "Sekolah Menengah Pertama (SMP)",
    "Sekolah Menengah Atas (SMA)",
    "Sekolah Menengah Kejuruan (SMK)",
    "Sekolah Luar Biasa (SLB)",
    "Lembaga Kursus",
    "Pendidikan Tinggi",
]

# Inisialisasi 3 Tab Menu
tab1, tab2, tab3 = st.tabs(
    [
        "📋 Tabel Rekapitulasi Utama",
        "🏫 Input & Daftar Detail Sekolah",
        "📂 Rincian per Jenjang Pendidikan",
    ]
)

with tab1:
  st.subheader("Rekapitulasi Satuan Pendidikan dan PTK")
  try:
    res = (
        supabase.table("tabel_rekap_pendidikan")
        .select("*")
        .order("id", desc=False)
        .execute()
    )
    df_rekap = pd.DataFrame(res.data)

    if not df_rekap.empty:
      if (
          "sudah_terdaftar" in df_rekap.columns
          and "jumlah_ptk" in df_rekap.columns
      ):
        df_rekap["Belum Terdaftar"] = (
            df_rekap["jumlah_ptk"] - df_rekap["sudah_terdaftar"]
        )
        df_rekap["Persentase"] = (
            df_rekap["sudah_terdaftar"]
            / df_rekap["jumlah_ptk"].replace(0, 1)
        ) * 100
        df_rekap["Persentase"] = df_rekap["Persentase"].round(2).astype(str) + "%"

      df_rekap = df_rekap.drop(columns=["created_at"], errors="ignore")
      st.dataframe(df_rekap, use_container_width=True, hide_index=True)

      st.markdown("---")
      st.subheader("📥 Unduh Laporan Rekapitulasi")

      col_dl1, col_dl2, col_dl3 = st.columns(3)

      with col_dl1:
        csv_data = df_rekap.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Unduh CSV",
            data=csv_data,
            file_name="rekap_monitoring_bpjs.csv",
            mime="text/csv",
        )

      with col_dl2:
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
          df_rekap.to_excel(writer, index=False, sheet_name="Rekap BPJS")
        excel_data = output_excel.getvalue()
        st.download_button(
            label="📊
