from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("Silakan login terlebih dahulu.")
  st.stop()

st.title("Monitoring Kepesertaan Berdasarkan Jenjang Pendidikan")
st.write(
    "Rekapitulasi jumlah satuan pendidikan, PTK, serta rincian daftar sekolah."
)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

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

tab1, tab2, tab3 = st.tabs(
    [
        "Tabel Rekapitulasi Utama",
        "Input & Daftar Detail Sekolah",
        "Rincian per Jenjang Pendidikan",
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

        tot_satuan = (
            df_rekap["jumlah_satuan_pendidikan"].sum()
            if "jumlah_satuan_pendidikan" in df_rekap.columns
            else 0
        )
        tot_ptk = df_rekap["jumlah_ptk"].sum()
        tot_sudah = df_rekap["sudah_terdaftar"].sum()
        tot_belum = df_rekap["Belum Terdaftar"].sum()
        tot_persen = round(
            (tot_sudah / tot_ptk * 100) if tot_ptk > 0 else 0, 2
        )

        df_rekap["Persentase"] = (
            df_rekap["sudah_terdaftar"]
            / df_rekap["jumlah_ptk"].replace(0, 1)
        ) * 100
        df_rekap["Persentase"] = df_rekap["Persentase"].round(2).astype(str) + "%"

        row_total = {
            "jenjang": "TOTAL KESELURUHAN",
            "jumlah_satuan_pendidikan": tot_satuan,
            "jumlah_ptk": tot_ptk,
            "sudah_terdaftar": tot_sudah,
            "Belum Terdaftar": tot_belum,
            "Persentase": f"{tot_persen}%",
        }
        for col in df_rekap.columns:
          if col not in row_total:
            row_total[col] = ""

        df_rekap = pd.concat(
            [df_rekap, pd.DataFrame([row_total])], ignore_index=True
        )

      df_rekap = df_rekap.drop(columns=["created_at"], errors="ignore")
      st.dataframe(df_rekap, use_container_width=True, hide_index=True)

      st.markdown("---")
      st.subheader("Unduh Laporan Rekapitulasi")

      col_dl1, col_dl2, col_dl3 = st.columns(3)

      with col_dl1:
        csv_data = df_rekap.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Unduh CSV",
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
            label="Unduh Excel",
            data=excel_data,
            file_name="rekap_monitoring_bpjs.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

      with col_dl3:
        buffer_pdf = BytesIO()
        doc = SimpleDocTemplate(
            buffer_pdf,
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

        table_data = [list(df_rekap.columns)]
        for _, row in df_rekap.iterrows():
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
                ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5, 0.5)),
                ("BACKGROUND", (0, -1), (-1, -1), (0.85, 0.90, 0.95)),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ])
        )
        elements.append(t)
        doc.build(elements)
        pdf_data = buffer_pdf.getvalue()

        st.download_button(
            label="Unduh PDF",
            data=pdf_data,
            file_name="rekap_monitoring_bpjs.pdf",
            mime="application/pdf",
        )
    else:
      st.info("Belum ada data rekap.")
  except Exception as e:
    st.error(f"Gagal memuat rekapitulasi: {e}")

with tab2:
  st.subheader("Pencatatan & Manajemen Nama Sekolah per Jenjang")

  with st.expander("Tambah Data Sekolah Baru"):
    with st.form("form_detail_sekolah"):
      pilih_jenjang = st.selectbox(
          "Pilih Jenjang / Jenis Satuan Pendidikan", list_jenjang
      )
      nama_sekolah = st.text_input("Nama Sekolah / Lembaga")
      alamat_sekolah = st.text_area("Alamat Sekolah")

      col_tot, col1, col2 = st.columns(3)
      with col_tot:
        input_total_ptk = st.number_input(
            "Jumlah Total PTK", min_value=0, value=0
        )
      with col1:
        input_sudah = st.number_input(
            "Jumlah Sudah Terdaftar", min_value=0, value=0
        )
      with col2:
        input_belum = st.number_input(
            "Jumlah Belum Terdaftar", min_value=0, value=0
        )

      keterangan_sekolah = st.text_input("Keterangan Tambahan")
      submit_sekolah = st.form_submit_button(
          "Simpan Data Sekolah", type="primary"
      )

      if submit_sekolah:
        if not nama_sekolah:
          st.error("Nama sekolah wajib diisi!")
        else:
          try:
            data_sekolah = {
                "jenjang": pilih_jenjang,
                "nama_sekolah": nama_sekolah,
                "alamat": alamat_sekolah,
                "jumlah_total_ptk": input_total_ptk,
                "jumlah_sudah": input_sudah,
                "jumlah_belum": input_belum,
                "keterangan": keterangan_sekolah,
            }
            supabase.table("tabel_detail_sekolah").insert(data_sekolah).execute()

            if input_sudah > 0:
              res_rekap = (
                  supabase.table("tabel_rekap_pendidikan")
                  .select("sudah_terdaftar")
                  .eq("jenjang", pilih_jenjang)
                  .execute()
              )
              if res_rekap.data:
                current_val = res_rekap.data[0].get("sudah_terdaftar", 0) or 0
                new_val = current_val + input_sudah
                supabase.table("tabel_rekap_pendidikan").update(
                    {"sudah_terdaftar": new_val}
                ).eq("jenjang", pilih_jenjang).execute()

            st.success("Data sekolah berhasil disimpan dan rekap diperbarui!")
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menyimpan data sekolah: {e}")

  st.markdown("---")
  st.subheader("Daftar Sekolah & Fitur Hapus Data")

  try:
    res_detail = (
        supabase.table("tabel_detail_sekolah")
        .select("*")
        .order("id", desc=False)
        .execute()
    )
    df_detail = pd.DataFrame(res_detail.data)

    if not df_detail.empty:
      df_detail = df_detail.drop(columns=["created_at"], errors="ignore")

      pilih_filter = st.selectbox(
          "Filter Berdasarkan Jenjang:", ["Semua Jenjang"] + list_jenjang
      )
      if pilih_filter != "Semua Jenjang":
        df_detail_filtered = df_detail[df_detail["jenjang"] == pilih_filter]
      else:
        df_detail_filtered = df_detail

      st.dataframe(df_detail_filtered, use_container_width=True, hide_index=True)

      st.markdown("### Hapus Data Sekolah")
      opsi_sekolah = {
          f"{row['nama_sekolah']} ({row['jenjang']}) - ID: {row['id']}": row[
              "id"
          ]
          for _, row in df_detail_filtered.iterrows()
      }

      if opsi_sekolah:
        pilih_hapus = st.selectbox(
            "Pilih sekolah yang ingin dihapus:", list(opsi_sekolah.keys())
        )

        if st.button("Hapus Data Terpilih", type="secondary"):
          target_id = opsi_sekolah[pilih_hapus]
          data_hapus = (
              supabase.table("tabel_detail_sekolah")
              .select("*")
              .eq("id", target_id)
              .execute()
          )

          if data_hapus.data:
            item = data_hapus.data[0]
            j_jenjang = item.get("jenjang")
            j_sudah = item.get("jumlah_
