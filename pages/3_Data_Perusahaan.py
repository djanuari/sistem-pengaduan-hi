import io
import pandas as pd
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning(
      "⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login."
  )
  st.stop()

st.set_page_config(
    page_title="Data Perusahaan & Pembinaan HI", page_icon="🏢", layout="wide"
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("🏢 Daftar Perusahaan & Pembinaan Hubungan Industrial")

# Opsi pilihan dropdown standar
opsi_ada = ["Ada", "Tidak Ada", "Dalam Proses"]
opsi_bpjs = [
    "Terdaftar Lengkap (Kesehatan & TK)",
    "Sebagian",
    "Belum Terdaftar",
]
opsi_status = ["Aktif", "Tidak Aktif", "Dalam Pengawasan / Pembinaan"]


def safe_str(val):
  return str(val) if val is not None and str(val) != "None" else ""


# Ambil data dari Supabase
def load_data():
  try:
    res = (
        supabase.table("tabel_perusahaan")
        .select("*")
        .order("id", desc=False)
        .execute()
    )
    return pd.DataFrame(res.data)
  except Exception as e:
    st.error(f"Gagal mengambil data perusahaan dari database: {e}")
    return pd.DataFrame()


df_raw = load_data()

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Daftar Perusahaan",
    "➕ Tambah Perusahaan",
    "✏️ Edit Data",
    "🗑️ Hapus Data",
])

# ==========================================
# TAB 1: DAFTAR PERUSAHAAN (TABEL & EKSPOR)
# ==========================================
with tab1:
  st.subheader("Rekapitulasi Data Perusahaan")

  if not df_raw.empty:
    # Filter pencarian cepat
    c_cari1, c_cari2 = st.columns([2, 1])
    kata_kunci = c_cari1.text_input(
        "🔍 Cari Nama Perusahaan / NIB / Alamat:", ""
    )
    filter_status = c_cari2.selectbox("Filter Status:", ["Semua"] + opsi_status)

    df_tampil = df_raw.copy()
    if kata_kunci.strip():
      mask = (
          df_tampil["nama_perusahaan"]
          .fillna("")
          .str.contains(kata_kunci, case=False)
          | df_tampil["nib"].fillna("").str.contains(kata_kunci, case=False)
          | df_tampil["alamat"].fillna("").str.contains(kata_kunci, case=False)
      )
      df_tampil = df_tampil[mask]

    if filter_status != "Semua":
      df_tampil = df_tampil[df_tampil["status"] == filter_status]

    # Tambahkan kolom No otomatis mulai dari 1
    df_tampil.insert(0, "No", range(1, len(df_tampil) + 1))

    # Susun dan ubah nama kolom sesuai format yang diminta
    kolom_mapping = {
        "No": "No",
        "nama_perusahaan": "Nama Perusahaan",
        "nib": "NIB",
        "alamat": "Alamat",
        "jumlah_pekerja": "Jumlah Pekerja",
        "pp": "PP",
        "pkb": "PKB",
        "lks_bipartit": "LKS Bipartit",
        "sp_sb": "SP/SB",
        "bpjs": "BPJS",
        "perselisihan": "Perselisihan",
        "phk": "PHK",
        "pembinaan": "Pembinaan",
        "status": "Status",
    }

    df_final = df_tampil[list(kolom_mapping.keys())].rename(
        columns=kolom_mapping
    )

    st.dataframe(df_final, use_container_width=True, hide_index=True)

    # Ringkasan singkat & Tombol Download Excel
    col_info, col_dl = st.columns([3, 1])
    col_info.caption(
        f"Total ditampilkan: **{len(df_final)}** perusahaan | Total pekerja:"
        f" **{int(df_final['Jumlah Pekerja'].fillna(0).sum()):,}** orang"
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      df_final.to_excel(writer, index=False, sheet_name="Data_Perusahaan")

    col_dl.download_button(
        label="📥 Unduh Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="Daftar_Perusahaan_HI.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )
  else:
    st.info(
        "Belum ada data perusahaan. Silakan tambahkan melalui tab **➕ Tambah"
        " Perusahaan**."
    )

# ==========================================
# TAB 2: TAMBAH PERUSAHAAN BARU
# ==========================================
with tab2:
  st.subheader("Input Data Perusahaan Baru")
  with st.form("form_tambah_perusahaan", clear_on_submit=True):
    c1, c2 = st.columns(2)
    nama_perusahaan = c1.text_input("Nama Perusahaan *")
    nib = c2.text_input("NIB (Nomor Induk Berusaha)")

    c3, c4 = st.columns([2, 1])
    alamat = c3.text_area("Alamat Perusahaan")
    jumlah_pekerja = c4.number_input("Jumlah Pekerja", min_value=0, step=1)

    st.markdown("**Kelengkapan Perangkat Hubungan Industrial**")
    k1, k2, k3, k4, k5 = st.columns(5)
    pp = k1.selectbox("PP (Peraturan Perusahaan)", opsi_ada)
    pkb = k2.selectbox("PKB", opsi_ada)
    lks_bipartit = k3.selectbox("LKS Bipartit", opsi_ada)
    sp_sb = k4.selectbox("SP/SB", opsi_ada)
    bpjs = k5.selectbox("BPJS", opsi_bpjs)

    st.markdown("**Catatan Kasus & Pembinaan**")
    p1, p2 = st.columns(2)
    perselisihan = p1.text_area("Perselisihan (Riwayat / Keterangan)")
    phk = p2.text_area("PHK (Jumlah / Keterangan Kasus PHK)")

    p3, p4 = st.columns([2, 1])
    pembinaan = p3.text_area("Pembinaan yang Telah Dilakukan")
    status = p4.selectbox("Status Perusahaan", opsi_status)

    submit_perusahaan = st.form_submit_button(
        "Simpan Data Perusahaan", type="primary"
    )

  if submit_perusahaan:
    if not nama_perusahaan.strip():
      st.error("Nama Perusahaan wajib diisi!")
    else:
      try:
        data_baru = {
            "nama_perusahaan": nama_perusahaan.strip(),
            "nib": nib.strip(),
            "alamat": alamat.strip(),
            "jumlah_pekerja": int(jumlah_pekerja),
            "pp": pp,
            "pkb": pkb,
            "lks_bipartit": lks_bipartit,
            "sp_sb": sp_sb,
            "bpjs": bpjs,
            "perselisihan": perselisihan.strip(),
            "phk": phk.strip(),
            "pembinaan": pembinaan.strip(),
            "status": status,
        }
        supabase.table("tabel_perusahaan").insert(data_baru).execute()
        st.success(
            f"Berhasil! Data **{nama_perusahaan}** telah ditambahkan ke"
            " database."
        )
        st.rerun()
      except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

# ==========================================
# TAB 3: EDIT DATA PERUSAHAAN
# ==========================================
with tab3:
  if not df_raw.empty:
    pilihan_dict = {
        f"{row['nama_perusahaan']} (NIB: {row['nib'] or '-'})": row["id"]
        for _, row in df_raw.iterrows()
    }
    label_pilih = st.selectbox(
        "Pilih Perusahaan yang Ingin Diedit:", list(pilihan_dict.keys())
    )
    id_pilih = pilihan_dict[label_pilih]
    row_edit = df_raw[df_raw["id"] == id_pilih].iloc[0]

    with st.form("form_edit_perusahaan"):
      ec1, ec2 = st.columns(2)
      u_nama = ec1.text_input(
          "Nama Perusahaan *", value=safe_str(row_edit["nama_perusahaan"])
      )
      u_nib = ec2.text_input("NIB", value=safe_str(row_edit["nib"]))

      ec3, ec4 = st.columns([2, 1])
      u_alamat = ec3.text_area("Alamat", value=safe_str(row_edit["alamat"]))
      u_pekerja = ec4.number_input(
          "Jumlah Pekerja",
          min_value=0,
          step=1,
          value=int(row_edit["jumlah_pekerja"] or 0),
      )

      st.markdown("**Kelengkapan Perangkat Hubungan Industrial**")
      ek1, ek2, ek3, ek4, ek5 = st.columns(5)
      u_pp = ek1.selectbox(
          "PP",
          opsi_ada,
          index=opsi_ada.index(row_edit["pp"])
          if row_edit["pp"] in opsi_ada
          else 0,
      )
      u_pkb = ek2.selectbox(
          "PKB",
          opsi_ada,
          index=opsi_ada.index(row_edit["pkb"])
          if row_edit["pkb"] in opsi_ada
          else 0,
      )
      u_lks = ek3.selectbox(
          "LKS Bipartit",
          opsi_ada,
          index=opsi_ada.index(row_edit["lks_bipartit"])
          if row_edit["lks_bipartit"] in opsi_ada
          else 0,
      )
      u_sp = ek4.selectbox(
          "SP/SB",
          opsi_ada,
          index=opsi_ada.index(row_edit["sp_sb"])
          if row_edit["sp_sb"] in opsi_ada
          else 0,
      )
      u_bpjs = ek5.selectbox(
          "BPJS",
          opsi_bpjs,
          index=opsi_bpjs.index(row_edit["bpjs"])
          if row_edit["bpjs"] in opsi_bpjs
          else 0,
      )

      st.markdown("**Catatan Kasus & Pembinaan**")
      ep1, ep2 = st.columns(2)
      u_perselisihan = ep1.text_area(
          "Perselisihan", value=safe_str(row_edit["perselisihan"])
      )
      u_phk = ep2.text_area("PHK", value=safe_str(row_edit["phk"]))

      ep3, ep4 = st.columns([2, 1])
      u_pembinaan = ep3.text_area(
          "Pembinaan", value=safe_str(row_edit["pembinaan"])
      )
      u_status = ep4.selectbox(
          "Status",
          opsi_status,
          index=opsi_status.index(row_edit["status"])
          if row_edit["status"] in opsi_status
          else 0,
      )

      if st.form_submit_button("Simpan Perubahan", type="primary"):
        if not u_nama.strip():
          st.error("Nama Perusahaan tidak boleh kosong!")
        else:
          try:
            data_upd = {
                "nama_perusahaan": u_nama.strip(),
                "nib": u_nib.strip(),
                "alamat": u_alamat.strip(),
                "jumlah_pekerja": int(u_pekerja),
                "pp": u_pp,
                "pkb": u_pkb,
                "lks_bipartit": u_lks,
                "sp_sb": u_sp,
                "bpjs": u_bpjs,
                "perselisihan": u_perselisihan.strip(),
                "phk": u_phk.strip(),
                "pembinaan": u_pembinaan.strip(),
                "status": u_status,
            }
            supabase.table("tabel_perusahaan").update(data_upd).eq(
                "id", id_pilih
            ).execute()
            st.success(f"Data **{u_nama}** berhasil diperbarui!")
            st.rerun()
          except Exception as e:
            st.error(f"Gagal memperbarui data: {e}")
  else:
    st.info("Belum ada data perusahaan untuk diedit.")

# ==========================================
# TAB 4: HAPUS DATA PERUSAHAAN
# ==========================================
with tab4:
  if not df_raw.empty:
    hapus_dict = {
        f"{row['nama_perusahaan']} (NIB: {row['nib'] or '-'})": row["id"]
        for _, row in df_raw.iterrows()
    }
    label_hapus = st.selectbox(
        "Pilih Perusahaan untuk DIHAPUS:",
        list(hapus_dict.keys()),
        key="hapus_perusahaan_unik",
    )
    id_hapus = hapus_dict[label_hapus]

    if st.button("🗑️ Hapus Permanen Data Perusahaan", type="secondary"):
      try:
        supabase.table("tabel_perusahaan").delete().eq("id", id_hapus).execute()
        st.success(f"Data **{label_hapus}** berhasil dihapus!")
        st.rerun()
      except Exception as e:
        st.error(f"Gagal menghapus data: {e}")
  else:
    st.info("Tidak ada data untuk dihapus.")
