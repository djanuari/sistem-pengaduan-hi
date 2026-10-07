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

# Inisialisasi Tab Menu
tab1, tab2 = st.tabs(
    ["📋 Tabel Rekapitulasi Utama", "🏫 Input & Daftar Detail Sekolah"]
)

with tab1:
  st.subheader("Rekapitulasi Satuan Pendidikan dan PTK")
  try:
    res = supabase.table("tabel_rekap_pendidikan").select("*").execute()
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

      st.dataframe(df_rekap, use_container_width=True)
    else:
      st.info("Belum ada data rekap.")
  except Exception as e:
    st.error(f"Gagal memuat rekapitulasi: {e}")

with tab2:
  st.subheader("Pencatatan & Manajemen Nama Sekolah per Jenjang")

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

  with st.expander("➕ Tambah Data Sekolah Baru"):
    with st.form("form_detail_sekolah"):
      pilih_jenjang = st.selectbox(
          "Pilih Jenjang / Jenis Satuan Pendidikan", list_jenjang
      )
      nama_sekolah = st.text_input("Nama Sekolah / Lembaga")
      alamat_sekolah = st.text_area("Alamat Sekolah")

      col1, col2 = st.columns(2)
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
    res_detail = supabase.table("tabel_detail_sekolah").select("*").execute()
    df_detail = pd.DataFrame(res_detail.data)

    if not df_detail.empty:
      pilih_filter = st.selectbox(
          "Filter Berdasarkan Jenjang:", ["Semua Jenjang"] + list_jenjang
      )
      if pilih_filter != "Semua Jenjang":
        df_detail_filtered = df_detail[df_detail["jenjang"] == pilih_filter]
      else:
        df_detail_filtered = df_detail

      st.dataframe(df_detail_filtered, use_container_width=True)

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
