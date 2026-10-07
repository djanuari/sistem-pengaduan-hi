import pandas as pd
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Silakan login terlebih dahulu.")
  st.stop()

st.title("🛡️ Monitoring Kepesertaan BPJS Ketenagakerjaan & Kesehatan")
st.write(
    "Halaman ini digunakan untuk mencatat dan memverifikasi status kepesertaan"
    " BPJS dari perusahaan atau pekerja yang berpekara."
)

# Inisialisasi koneksi Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# Form Input Data BPJS Baru
with st.expander("➕ Tambah / Perbarui Data Kepesertaan BPJS"):
  with st.form("form_bpjs"):
    nama_perusahaan = st.text_input("Nama Perusahaan / Terlapor")
    no_pendaftaran = st.text_input(
        "Nomor Pendaftaran / NPP (Nomor Pendaftaran Perusahaan)"
    )

    col1, col2 = st.columns(2)
    with col1:
      bpjs_tk = st.selectbox(
          "Status BPJS Ketenagakerjaan",
          ["Aktif", "Tidak Aktif", "Belum Terdaftar", "Sebagian Belum Didaftarkan"],
      )
      jml_tenaga_kerja = st.number_input(
          "Jumlah Tenaga Kerja Terdaftar", min_value=0, value=0
      )
    with col2:
      bpjs_kes = st.selectbox(
          "Status BPJS Kesehatan",
          ["Aktif", "Tidak Aktif", "Belum Terdaftar"],
      )
      keterangan_tunggakan = st.text_input(
          "Catatan / Estimasi Tunggakan (Jika Ada)"
      )

    simpan_bpjs = st.form_submit_button("Simpan Data BPJS", type="primary")

    if simpan_bpjs:
      if not nama_perusahaan:
        st.error("Nama perusahaan wajib diisi!")
      else:
        try:
          data_bpjs = {
              "nama_perusahaan": nama_perusahaan,
              "no_pendaftaran": no_pendaftaran,
              "bpjs_tk": bpjs_tk,
              "jml_tenaga_kerja": jml_tenaga_kerja,
              "bpjs_kes": bpjs_kes,
              "keterangan_tunggakan": keterangan_tunggakan,
          }
          # Pastikan tabel 'tabel_bpjs' sudah dibuat di Supabase SQL Editor Anda
          supabase.table("tabel_bpjs").insert(data_bpjs).execute()
          st.success(
              f"Data kepesertaan BPJS untuk {nama_perusahaan} berhasil"
              " disimpan!"
          )
        except Exception as e:
          st.error(
              f"Gagal menyimpan data (pastikan tabel 'tabel_bpjs' ada): {e}"
          )

st.markdown("---")
st.subheader("📋 Daftar Rekapitulasi Kepesertaan BPJS")

# Menampilkan Data dari Supabase
try:
  res = supabase.table("tabel_bpjs").select("*").execute()
  df_bpjs = pd.DataFrame(res.data)
  if not df_bpjs.empty:
    st.dataframe(df_bpjs, use_container_width=True)
  else:
    st.info("Belum ada data kepesertaan BPJS yang tercatat.")
except Exception as e:
  st.info(
      "Tabel kepesertaan BPJS di database belum tersedia. Silakan buat tabel"
      " 'tabel_bpjs' terlebih dahulu di [Supabase](https://supabase.com/dashboard/project/sgaxrdtgiynemnrwyisb/sql) SQL Editor."
  )
