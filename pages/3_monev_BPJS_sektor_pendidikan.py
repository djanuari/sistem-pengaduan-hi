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
                  ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5, 0.5)),
              ])
          )
          elements.append(t)
          doc.build(elements)
          buffer.seek(0)
          return buffer.getvalue()

        pdf_data = generate_pdf(df_rekap)
        st.download_button(
            label="📑 Unduh PDF",
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

  with st.expander("➕ Tambah Data Sekolah Baru"):
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

            st.success(
                f"Data sekolah **{nama_sekolah}** berhasil disimpan dan rekap"
                " diperbarui!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menyimpan data sekolah: {e}")

  st.markdown("---")
  st.subheader("📋 Daftar Sekolah & Fitur Hapus Data")

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

      st.markdown("### 🗑️ Hapus Data Sekolah")
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

        if st.button("🗑️ Hapus Data Terpilih", type="secondary"):
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
            j_sudah = item.get("jumlah_sudah", 0) or 0

            supabase.table("tabel_detail_sekolah").delete().eq(
                "id", target_id
            ).execute()

            if j_sudah > 0 and j_jenjang:
              res_rekap = (
                  supabase.table("tabel_rekap_pendidikan")
                  .select("sudah_terdaftar")
                  .eq("jenjang", j_jenjang)
                  .execute()
              )
              if res_rekap.data:
                current_val = res_rekap.data[0].get("sudah_terdaftar", 0) or 0
                new_val = max(0, current_val - j_sudah)

                supabase.table("tabel_rekap_pendidikan").update(
                    {"sudah_terdaftar": new_val}
                ).eq("jenjang", j_jenjang).execute()

            st.success(
                "Data sekolah berhasil dihapus dan rekapitulasi diperbarui!"
            )
            st.rerun()
      else:
        st.info("Tidak ada data pada filter jenjang ini.")
    else:
      st.info("Belum ada data detail sekolah yang diinput.")
  except Exception as e:
    st.info(f"Terjadi kesalahan saat memuat data detail: {e}")

with tab3:
  st.subheader("📂 Rincian Rekapitulasi Berdasarkan Jenis Jenjang Pendidikan")
  st.write(
      "Pilih salah satu jenis jenjang pendidikan di bawah untuk melihat rincian"
      " satuan pendidikan dan total PTK-nya secara spesifik."
  )

  pilih_jenjang_detail = st.selectbox(
      "Pilih Jenjang Pendidikan:", list_jenjang, key="select_jenjang_detail"
  )

  try:
    # Ambil data rincian sekolah sesuai jenjang yang dipilih
    res_jenjang_terpilih = (
        supabase.table("tabel_detail_sekolah")
        .select("*")
        .eq("jenjang", pilih_jenjang_detail)
        .order("id", desc=False)
        .execute()
    )
    df_j_terpilih = pd.DataFrame(res_jenjang_terpilih.data)

    # Ambil data rekap utama untuk jenjang tersebut
    res_rekap_single = (
        supabase.table("tabel_rekap_pendidikan")
        .select("*")
        .eq("jenjang", pilih_jenjang_detail)
        .execute()
    )

    st.markdown(f"### Ringkasan untuk Jenjang: **{pilih_jenjang_detail}**")

    if res_rekap_single.data:
      data_R = res_rekap_single.data[0]
      tot_satuan = data_R.get("jumlah_satuan_pendidikan", 0) or 0
      tot_ptk = data_R.get("jumlah_ptk", 0) or 0
      sudah_reg = data_R.get("sudah_terdaftar", 0) or 0
      belum_reg = max(0, tot_ptk - sudah_reg)
      persen_reg = round((sudah_reg / tot_ptk * 100) if tot_ptk > 0 else 0, 2)

      mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
      mcol1.metric("Jumlah Satuan", tot_satuan)
      mcol2.metric("Jumlah PTK", tot_ptk)
      mcol3.metric("Sudah Terdaftar", sudah_reg)
      mcol4.metric("Belum Terdaftar", belum_reg)
      mcol5.metric("Persentase", f"{persen_reg}%")

    st.markdown("---")
    st.markdown(f"**Daftar Sekolah / Lembaga pada Jenjang {pilih_jenjang_detail}:**")

    if not df_j_terpilih.empty:
      df_j_terpilih = df_j_terpilih.drop(columns=["created_at"], errors="ignore")
      st.dataframe(df_j_terpilih, use_container_width=True, hide_index=True)
    else:
      st.info(
          f"Belum ada data sekolah terdaftar untuk jenjang {pilih_jenjang_detail}."
      )

  except Exception as e:
    st.error(f"Gagal memuat rincian jenjang: {e}")
