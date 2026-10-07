import pandas as pd
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

# Tab Menu untuk Tampilan Rekap & Input Detail Sekolah
tab1, tab2 = st.tabs(
    ["📋 Tabel Rekapitulasi Utama", "🏫 Input & Daftar Detail Sekolah"]
)

with tab1:
  st.subheader("Rekapitulasi Satuan Pendidikan dan PTK")
  try:
    res = supabase.table("tabel_rekap_pendidikan").select("*").execute()
    df_rekap = pd.DataFrame(res.data)

    if not df_rekap.empty:
      # Hitung Persentase otomatis jika kolom tersedia
      if (
          "sudah_terdaftar" in df_rekap.columns
          and "jumlah_satuan_pendidikan" in df_rekap.columns
      ):
        df_rekap["Persentase"] = (
            df_rekap["sudah_terdaftar"]
            / df_rekap["jumlah_satuan_pendidikan"].replace(0, 1)
        ) * 100
        df_rekap["Persentase"] = df_rekap["Persentase"].round(2).astype(str) + "%"

      st.dataframe(df_rekap, use_container_width=True)
    else:
      st.info(
          "Belum ada data rekap. Anda dapat mengisi data awal atau melakukan"
          " sinkronisasi."
      )
  except Exception as e:
    st.error(f"Gagal memuat rekapitulasi: {e}")

with tab2:
  st.subheader("Pencatatan Nama Sekolah per Jenjang")

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

  with st.form("form_detail_sekolah"):
    pilih_jenjang = st.selectbox("Pilih Jenjang / Jenis Satuan Pendidikan", list_jenjang)
    nama_sekolah = st.text_input("Nama Sekolah / Lembaga")
    alamat_sekolah = st.text_area("Alamat Sekolah")
    status_pendaftaran = st.selectbox(
        "Status Kepesertaan", ["Sudah Terdaftar", "Belum Terdaftar"]
    )
    keterangan_sekolah = st.text_input("Keterangan Tambahan")

    submit_sekolah = st.form_submit_button("Simpan Data Sekolah", type="primary")

    if submit_sekolah:
      if not nama_sekolah:
        st.error("Nama sekolah wajib diisi!")
      else:
        try:
          data_sekolah = {
              "jenjang": pilih_jenjang,
              "nama_sekolah": nama_sekolah,
              "alamat": alamat_sekolah,
              "status_terdaftar": status_pendaftaran,
              "keterangan": keterangan_sekolah,
          }
          supabase.table("tabel_detail_sekolah").insert(data_sekolah).execute()
          st.success(f"Data sekolah **{nama_sekolah}** berhasil disimpan!")
        except Exception as e:
          st.error(f"Gagal menyimpan data sekolah: {e}")

  st.markdown("---")
  st.subheader("Daftar Sekolah yang Telah Didata")
  try:
    res_detail = supabase.table("tabel_detail_sekolah").select("*").execute()
    df_detail = pd.DataFrame(res_detail.data)
    if not df_detail.empty:
      # Filter berdasarkan jenjang
      pilih_filter = st.selectbox(
          "Filter Berdasarkan Jenjang:", ["Semua Jenjang"] + list_jenjang
      )
      if pilih_filter != "Semua Jenjang":
        df_detail = df_detail[df_detail["jenjang"] == pilih_filter]

      st.dataframe(df_detail, use_container_width=True)
    else:
      st.info("Belum ada data detail sekolah yang diinput.")
  except Exception as e:
    st.info("Tabel detail sekolah belum siap.")
