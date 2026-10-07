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

# Inisialisasi Tab Menu
tab1, tab2 = st.tabs(
    ["📋 Tabel Rekapitulasi Utama", "🏫 Input & Daftar Detail Sekolah"]
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
            label="📊 Unduh Excel",
            data=excel_data,
            file_name="rekap_monitoring_bpjs.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

      with col_dl3:
        def generate_pdf(df):
          buffer = BytesIO()
          doc = SimpleDocTemplate(
              buffer,
              pagesize=landscape(A4),
              rightMargin=30,
              leftMargin=30,
              topMargin=30,
              bottomMargin=30,
          )
          elements = []
          styles = getSampleStyleSheet()
          title_style = ParagraphStyle(
              "TitleStyle",
              parent=styles["Heading1"],
              fontSize=14,
              alignment=1,
              spaceAfter=15,
          )

          elements.append(
              Paragraph(
                  "Laporan Rekapitulasi Monitoring BPJS Sektor Pendidikan",
                  title_style,
              )
          )
          elements.append(Spacer(1, 10))

          table_data = [list(df.columns)]
          for _, row in df.iterrows():
            table_data.append([str(val) for val in row.values])

          t = Table(table_data)
          t.setStyle(
              TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), (0.2, 0.4, 0.6)),
                  ("TEXTCOLOR", (0, 0), (-1, 0), (1, 1, 1)),
                  ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("FONTSIZE", (0, 0), (-1, -1), 8),
                  ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                  ("BACKGROUND", (0, 1), (-1, -1), (0.95, 0.95, 0.95)),
                  ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5,
