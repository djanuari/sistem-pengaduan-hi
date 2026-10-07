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
    pilih_jenjang = st.selectbox(
        "Pilih Jenjang / Jenis Satuan Pendidikan", list_jenjang
    )
    nama_sekolah = st.text_input("Nama Sekolah / Lembaga")
    alamat_sekolah = st.text_area("Alamat Sekolah")
    status_pendaftaran = st.selectbox(
        "Status Kepesertaan", ["Sudah Terdaftar", "Belum Terdaftar"]
    )
    jumlah_ptk_sekolah = st.number_input(
        "Jumlah PTK di Sekolah Ini", min_value=0, value=0
    )
    keterangan_sekolah = st.text_input("Keterangan Tambahan")

    submit_sekolah = st.form_submit_button("Simpan Data Sekolah", type="primary")

    if submit_sekolah:
      if not nama_sekolah:
        st.error("Nama sekolah wajib diisi!")
      else:
        try:
          # 1. Simpan data detail sekolah
          data_sekolah = {
              "jenjang": pilih_jenjang,
              "nama_sekolah": nama_sekolah,
              "alamat": alamat_sekolah,
              "status_terdaftar": status_pendaftaran,
              "jumlah_ptk": jumlah_ptk_sekolah,
              "keterangan": keterangan_sekolah,
          }
          supabase.table("tabel_detail_sekolah").insert(data_sekolah).execute()

          # 2. Jika statusnya "Sudah Terdaftar", update penambahan jumlah PTK ke tabel rekap utama
          if status_pendaftaran == "Sudah Terdaftar" and jumlah_ptk_sekolah > 0:
            # Ambil data rekap saat ini untuk jenjang tersebut
            res_rekap = (
                supabase.table("tabel_rekap_pendidikan")
                .select("sudah_terdaftar")
                .eq("jenjang", pilih_jenjang)
                .execute()
            )
            if res_rekap.data:
              current_val = res_rekap.data[0].get("sudah_terdaftar", 0) or 0
              new_val = current_val + jumlah_ptk_sekolah

              # Update ke database
              supabase.table("tabel_rekap_pendidikan").update(
                  {"sudah_terdaftar": new_val}
              ).eq("jenjang", pilih_jenjang).execute()

          st.success(
              f"Data sekolah **{nama_sekolah}** berhasil disimpan dan jumlah"
              " PTK terdaftar diperbarui!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Gagal menyimpan data sekolah: {e}")
