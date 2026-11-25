import datetime
import io
import math
from fpdf import FPDF
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

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("🏢 Daftar Perusahaan & Pembinaan Hubungan Industrial")

opsi_ada = ["Ada", "Tidak Ada", "Dalam Proses"]
opsi_bpjs = ["Sudah", "Belum"]
opsi_status = ["Aktif", "Tidak Aktif", "Dalam Pengawasan / Pembinaan"]


def safe_str(val):
  return str(val) if val is not None and str(val) != "None" else ""


# Konversi nilai BPJS lama (jika ada di database) agar cocok dengan opsi 'Sudah' / 'Belum'
def normalisasi_bpjs(val):
  s = safe_str(val).strip()
  if s in ["Sudah", "Terdaftar Lengkap (Kesehatan & TK)", "Sebagian"]:
    return "Sudah"
  return "Belum"


# Fungsi helper untuk membersihkan mode edit sekaligus mereset seleksi baris tabel
def tutup_mode_edit():
  st.session_state.edit_perusahaan_id = None
  if "tabel_daftar_perusahaan_klik" in st.session_state:
    del st.session_state["tabel_daftar_perusahaan_klik"]


def generate_pdf_perusahaan(df: pd.DataFrame) -> bytes:
  pdf = FPDF(orientation="L", unit="mm", format="A4")
  pdf.set_auto_page_break(auto=True, margin=12)
  pdf.add_page()

  pdf.set_font("Helvetica", "B", 13)
  pdf.cell(
      0,
      8,
      "REKAPITULASI DATA PERUSAHAAN & PEMBINAAN HUBUNGAN INDUSTRIAL",
      ln=True,
      align="C",
  )
  pdf.set_font("Helvetica", "", 9)
  tgl_cetak = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
  pdf.cell(
      0,
      6,
      f"Dicetak pada: {tgl_cetak} | Total Perusahaan: {len(df):,}",
      ln=True,
      align="C",
  )
  pdf.ln(4)

  col_widths = [
      7,
      28,
      17,
      26,
      18,
      23,
      12,
      12,
      12,
      14,
      12,
      12,
      21,
      18,
      20,
      15,
  ]
  headers = [
      "No",
      "Nama Perusahaan",
      "NIB",
      "Alamat",
      "No. Telp",
      "Email",
      "Pekerja",
      "PP",
      "PKB",
      "LKS Bip.",
      "SP/SB",
      "BPJS",
      "Perselisihan",
      "PHK",
      "Pembinaan",
      "Status",
  ]

  def draw_table_header():
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths, headers):
      pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 6)

  draw_table_header()

  for idx, row in df.iterrows():
    if pdf.get_y() > 185:
      pdf.add_page()
      draw_table_header()

    row_vals = [
        str(row["No"]),
        str(row["Nama Perusahaan"])[:24],
        str(row["NIB"])[:13],
        str(row["Alamat"])[:22],
        str(row["No. Telepon"])[:14],
        str(row["Email"])[:19],
        str(row["Jumlah Pekerja"]),
        str(row["PP"])[:9],
        str(row["PKB"])[:9],
        str(row["LKS Bipartit"])[:9],
        str(row["SP/SB"])[:9],
        str(row["BPJS"])[:9],
        str(row["Perselisihan"])[:17],
        str(row["PHK"])[:14],
        str(row["Pembinaan"])[:16],
        str(row["Status"])[:11],
    ]
    row_vals = [v.encode("latin-1", "replace").decode("latin-1") for v in row_vals]

    fill = idx % 2 == 1
    if fill:
      pdf.set_fill_color(245, 247, 250)

    aligns = [
        "C",
        "L",
        "C",
        "L",
        "L",
        "L",
        "R",
        "C",
        "C",
        "C",
        "C",
        "C",
        "L",
        "L",
        "L",
        "C",
    ]
    for w, val, al in zip(col_widths, row_vals, aligns):
      pdf.cell(w, 6, val, border=1, align=al, fill=fill)
    pdf.ln()

  return bytes(pdf.output())


# Ambil SELURUH data dari Supabase tanpa batas 1.000 baris
def load_data():
  try:
    all_data = []
    batch_size = 1000
    offset = 0

    while True:
      res = (
          supabase.table("tabel_perusahaan")
          .select("*")
          .order("id", desc=False)
          .range(offset, offset + batch_size - 1)
          .execute()
      )
      batch = res.data or []
      all_data.extend(batch)

      if len(batch) < batch_size:
        break
      offset += batch_size

    return pd.DataFrame(all_data)
  except Exception as e:
    st.error(f"Gagal mengambil data perusahaan dari database: {e}")
    return pd.DataFrame()


df_raw = load_data()

if "edit_perusahaan_id" not in st.session_state:
  st.session_state.edit_perusahaan_id = None

# ==========================================
# MODE EDIT CEPAT DI TAB YANG SAMA (TANPA BUKA JENDELA BARU)
# ==========================================
if st.session_state.edit_perusahaan_id is not None and not df_raw.empty:
  id_target = st.session_state.edit_perusahaan_id
  df_match = df_raw[df_raw["id"] == id_target]

  if not df_match.empty:
    row_edit = df_match.iloc[0]

    col_back, col_title = st.columns([1.2, 4])
    if col_back.button(
        "⬅️ Kembali ke Daftar",
        key="btn_kembali_atas",
        use_container_width=True,
    ):
      tutup_mode_edit()
      st.rerun()

    col_title.subheader(
        f"✏️ Edit Data Perusahaan: {safe_str(row_edit['nama_perusahaan'])}"
    )

    with st.form("form_edit_langsung"):
      ec1, ec2 = st.columns(2)
      u_nama = ec1.text_input(
          "Nama Perusahaan *", value=safe_str(row_edit["nama_perusahaan"])
      )
      u_nib = ec2.text_input("NIB", value=safe_str(row_edit["nib"]))

      ec3, ec4 = st.columns(2)
      u_telp = ec3.text_input(
          "Nomor Telepon", value=safe_str(row_edit.get("no_telp", ""))
      )
      u_email = ec4.text_input(
          "Email Perusahaan", value=safe_str(row_edit.get("email", ""))
      )

      ec5, ec6 = st.columns([2, 1])
      u_alamat = ec5.text_area("Alamat", value=safe_str(row_edit["alamat"]))
      u_pekerja = ec6.number_input(
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
      bpjs_awal = normalisasi_bpjs(row_edit.get("bpjs", "Belum"))
      u_bpjs = ek5.selectbox(
          "BPJS",
          opsi_bpjs,
          index=opsi_bpjs.index(bpjs_awal),
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

      b_simpan, b_batal = st.columns([1, 1])
      simpan_klik = b_simpan.form_submit_button(
          "💾 Simpan Perubahan", type="primary", use_container_width=True
      )
      batal_klik = b_batal.form_submit_button(
          "Batal & Kembali", use_container_width=True
      )

    if batal_klik:
      tutup_mode_edit()
      st.rerun()

    if simpan_klik:
      if not u_nama.strip():
        st.error("Nama Perusahaan tidak boleh kosong!")
      else:
        try:
          data_upd = {
              "nama_perusahaan": u_nama.strip(),
              "nib": u_nib.strip(),
              "alamat": u_alamat.strip(),
              "no_telp": u_telp.strip(),
              "email": u_email.strip(),
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
              "id", id_target
          ).execute()
          tutup_mode_edit()
          st.success(f"Data **{u_nama}** berhasil diperbarui!")
          st.rerun()
        except Exception as e:
          st.error(f"Gagal memperbarui data: {e}")

    st.stop()
  else:
    tutup_mode_edit()

# ==========================================
# TAMPILAN UTAMA (6 TAB)
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Daftar Perusahaan",
    "➕ Tambah Perusahaan",
    "📤 Impor Excel",
    "✏️ Edit Data",
    "🗑️ Hapus Data",
    "🔍 Cek Duplikat",
])

# ==========================================
# TAB 1: DAFTAR PERUSAHAAN (KLIK BARIS -> EDIT) & EKSPOR
# ==========================================
with tab1:
  st.subheader("Rekapitulasi Data Perusahaan")
  st.caption(
      "💡 **Tips:** Klik pada baris (atau kotak centang di sebelah kiri"
      " baris) perusahaan mana pun di tabel untuk langsung membuka formulir"
      " editnya."
  )

  if not df_raw.empty:
    for col_cek in ["no_telp", "email"]:
      if col_cek not in df_raw.columns:
        df_raw[col_cek] = ""

    c_cari1, c_cari2, c_cari3 = st.columns([2, 1, 1])
    kata_kunci = c_cari1.text_input(
        "🔍 Cari Nama Perusahaan / NIB / Alamat / Email / No. Telepon:", ""
    )
    filter_status = c_cari2.selectbox("Filter Status:", ["Semua"] + opsi_status)
    opsi_baris = [100, 250, 500, 1000, "Semua"]
    baris_per_halaman = c_cari3.selectbox(
        "Baris per halaman:", opsi_baris, index=2
    )

    df_tampil = df_raw.copy()
    if kata_kunci.strip():
      mask = (
          df_tampil["nama_perusahaan"]
          .fillna("")
          .str.contains(kata_kunci, case=False)
          | df_tampil["nib"].fillna("").str.contains(kata_kunci, case=False)
          | df_tampil["alamat"].fillna("").str.contains(kata_kunci, case=False)
          | df_tampil["no_telp"].fillna("").str.contains(kata_kunci, case=False)
          | df_tampil["email"].fillna("").str.contains(kata_kunci, case=False)
      )
      df_tampil = df_tampil[mask]

    if filter_status != "Semua":
      df_tampil = df_tampil[df_tampil["status"] == filter_status]

    # Selaraskan tampilan kolom BPJS menjadi 'Sudah' / 'Belum'
    df_tampil["bpjs"] = df_tampil["bpjs"].apply(normalisasi_bpjs)

    df_tampil = df_tampil.reset_index(drop=True)
    if "No" in df_tampil.columns:
      df_tampil = df_tampil.drop(columns=["No"])
    df_tampil.insert(0, "No", list(range(1, len(df_tampil) + 1)))

    kolom_mapping = {
        "No": "No",
        "nama_perusahaan": "Nama Perusahaan",
        "nib": "NIB",
        "alamat": "Alamat",
        "no_telp": "No. Telepon",
        "email": "Email",
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
    df_final.index = range(1, len(df_final) + 1)

    total_data = len(df_final)

    if baris_per_halaman == "Semua" or total_data == 0:
      total_halaman = 1
      halaman_aktif = 1
      start_row = 0
      end_row = total_data
      df_halaman = df_final
      mulai_idx = 1 if total_data > 0 else 0
      akhir_idx = total_data
    else:
      total_halaman = max(1, math.ceil(total_data / baris_per_halaman))

      if "halaman_perusahaan" not in st.session_state:
        st.session_state.halaman_perusahaan = 1
      if st.session_state.halaman_perusahaan > total_halaman:
        st.session_state.halaman_perusahaan = 1

      nav1, nav2, nav3, nav4 = st.columns([1, 2, 1, 2])
      with nav1:
        if st.button(
            "⬅️ Sebelumnya",
            disabled=(st.session_state.halaman_perusahaan <= 1),
            use_container_width=True,
        ):
          st.session_state.halaman_perusahaan -= 1
          st.rerun()

      with nav2:
        halaman_dipilih = st.number_input(
            f"Halaman (dari {total_halaman}):",
            min_value=1,
            max_value=total_halaman,
            value=st.session_state.halaman_perusahaan,
            step=1,
            label_visibility="collapsed",
        )
        if halaman_dipilih != st.session_state.halaman_perusahaan:
          st.session_state.halaman_perusahaan = halaman_dipilih
          st.rerun()

      with nav3:
        if st.button(
            "Berikutnya ➡️",
            disabled=(st.session_state.halaman_perusahaan >= total_halaman),
            use_container_width=True,
        ):
          st.session_state.halaman_perusahaan += 1
          st.rerun()

      halaman_aktif = st.session_state.halaman_perusahaan
      start_row = (halaman_aktif - 1) * baris_per_halaman
      end_row = min(start_row + baris_per_halaman, total_data)
      df_halaman = df_final.iloc[start_row:end_row]
      mulai_idx = start_row + 1
      akhir_idx = end_row

      with nav4:
        st.markdown(
            f"<div style='padding-top: 6px;'>Halaman <b>{halaman_aktif}</b>"
            f" dari <b>{total_halaman}</b> (Baris"
            f" <b>{mulai_idx:,}–{akhir_idx:,}</b>)</div>",
            unsafe_allow_html=True,
        )

    event_tabel = st.dataframe(
        df_halaman,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tabel_daftar_perusahaan_klik",
    )

    if event_tabel and event_tabel.selection and event_tabel.selection.rows:
      baris_terpilih_lokal = event_tabel.selection.rows[0]
      indeks_global = start_row + baris_terpilih_lokal
      if indeks_global < len(df_tampil):
        id_perusahaan_klik = int(df_tampil.iloc[indeks_global]["id"])
        st.session_state.edit_perusahaan_id = id_perusahaan_klik
        st.rerun()

    st.caption(
        f"Menampilkan baris **{mulai_idx:,}–{akhir_idx:,}** dari total"
        f" **{total_data:,}** perusahaan | Total pekerja keseluruhan:"
        f" **{int(df_final['Jumlah Pekerja'].fillna(0).sum()):,}** orang"
    )

    st.markdown("**Ekspor Seluruh Data Terfilter (Semua Halaman):**")
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
      df_final.to_excel(writer, index=False, sheet_name="Data_Perusahaan")

    col_dl1.download_button(
        label=f"📗 Unduh Excel ({total_data:,} data)",
        data=buffer_excel.getvalue(),
        file_name="Daftar_Perusahaan_HI.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    csv_data = df_final.to_csv(index=False).encode("utf-8-sig")
    col_dl2.download_button(
        label=f"📄 Unduh CSV ({total_data:,} data)",
        data=csv_data,
        file_name="Daftar_Perusahaan_HI.csv",
        mime="text/csv",
        use_container_width=True,
    )

    pdf_bytes = generate_pdf_perusahaan(df_final)
    col_dl3.download_button(
        label=f"📕 Unduh PDF ({total_data:,} data)",
        data=pdf_bytes,
        file_name="Daftar_Perusahaan_HI.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
  else:
    st.info(
        "Belum ada data perusahaan. Silakan tambahkan melalui tab **➕ Tambah"
        " Perusahaan** atau **📤 Impor Excel**."
    )

# ==========================================
# TAB 2: TAMBAH PERUSAHAAN BARU (SATUAN)
# ==========================================
with tab2:
  st.subheader("Input Data Perusahaan Baru")
  with st.form("form_tambah_perusahaan", clear_on_submit=True):
    c1, c2 = st.columns(2)
    nama_perusahaan = c1.text_input("Nama Perusahaan *")
    nib = c2.text_input("NIB (Nomor Induk Berusaha)")

    c3, c4 = st.columns(2)
    no_telp = c3.text_input("Nomor Telepon")
    email = c4.text_input("Email Perusahaan")

    c5, c6 = st.columns([2, 1])
    alamat = c5.text_area("Alamat Perusahaan")
    jumlah_pekerja = c6.number_input("Jumlah Pekerja", min_value=0, step=1)

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
            "no_telp": no_telp.strip(),
            "email": email.strip(),
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
# TAB 3: IMPOR MASSAL DARI FILE EXCEL
# ==========================================
with tab3:
  st.subheader("Impor Daftar Perusahaan dari File Excel")
  st.info(
      "Unggah file Excel (`.xlsx` / `.xls`) Anda, lalu pasangkan kolom yang"
      " sesuai untuk **Nama Perusahaan**, **Alamat**, **Nomor Telepon**, dan"
      " **Email**. Jika salah satu kolom tidak ada di file Excel, pilih"
      " **'(Tidak ada / Kosongkan)'**."
  )

  df_template = pd.DataFrame({
      "Nama Perusahaan": [
          "PT Contoh Sejahtera",
          "CV Maju Bersama",
      ],
      "Alamat": [
          "Jl. Jenderal Sudirman No. 10, Kendari",
          "Jl. Ahmad Yani No. 25, Kendari",
      ],
      "No. Telepon": ["081234567890", "082345678901"],
      "Email": ["hrd@contohsejahtera.co.id", "admin@majubersama.com"],
  })
  buf_tpl = io.BytesIO()
  with pd.ExcelWriter(buf_tpl, engine="openpyxl") as writer:
    df_template.to_excel(writer, index=False, sheet_name="Template")

  st.download_button(
      label="📥 Unduh Contoh Format Excel (.xlsx)",
      data=buf_tpl.getvalue(),
      file_name="Template_Impor_Perusahaan.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )

  uploaded_excel = st.file_uploader(
      "Pilih File Excel Daftar Perusahaan:", type=["xlsx", "xls"]
  )

  if uploaded_excel is not None:
    try:
      df_up = pd.read_excel(uploaded_excel)
      df_up = df_up.dropna(how="all")

      if df_up.empty:
        st.warning("File Excel yang diunggah kosong.")
      else:
        st.write(f"Pratinjau data ({len(df_up):,} baris ditemukan):")
        df_preview = df_up.head(10).reset_index(drop=True).copy()
        if "No" in df_preview.columns:
          df_preview = df_preview.drop(columns=["No"])
        df_preview.insert(0, "No", list(range(1, len(df_preview) + 1)))
        df_preview.index = range(1, len(df_preview) + 1)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)

        kolom_excel = list(df_up.columns)
        opsi_opsional = ["(Tidak ada / Kosongkan)"] + kolom_excel

        def cari_indeks_awal(daftar_kolom, kata_kunci_list, default_idx=0):
          for idx, col in enumerate(daftar_kolom):
            nama_col = str(col).strip().lower()
            if any(k in nama_col for k in kata_kunci_list):
              return idx
          return default_idx

        idx_nama = cari_indeks_awal(kolom_excel, ["nama", "perusahaan"], 0)
        idx_alamat = cari_indeks_awal(opsi_opsional, ["alamat", "address"], 0)
        idx_telp = cari_indeks_awal(
            opsi_opsional, ["telp", "telepon", "hp", "kontak", "wa"], 0
        )
        idx_email = cari_indeks_awal(opsi_opsional, ["email", "surel"], 0)

        st.markdown("**Pasangkan Kolom Excel ke Database:**")
        m1, m2 = st.columns(2)
        kolom_nama = m1.selectbox(
            "Kolom Nama Perusahaan (Wajib) *:",
            kolom_excel,
            index=idx_nama,
        )
        kolom_alamat = m2.selectbox(
            "Kolom Alamat:",
            opsi_opsional,
            index=idx_alamat,
        )

        m3, m4 = st.columns(2)
        kolom_telp = m3.selectbox(
            "Kolom Nomor Telepon:",
            opsi_opsional,
            index=idx_telp,
        )
        kolom_email = m4.selectbox(
            "Kolom Email:",
            opsi_opsional,
            index=idx_email,
        )

        lewati_duplikat = st.checkbox(
            "Lewati nama perusahaan yang sudah ada di database (cegah data"
            " ganda)",
            value=True,
        )

        if st.button("🚀 Mulai Impor ke Database", type="primary"):
          existing_names = set()
          if not df_raw.empty and "nama_perusahaan" in df_raw.columns:
            existing_names = {
                str(n).strip().lower()
                for n in df_raw["nama_perusahaan"].dropna()
            }

          records_to_insert = []
          jumlah_dilewati = 0

          def ambil_nilai_terpilih(baris, pilihan_kolom):
            if pilihan_kolom == "(Tidak ada / Kosongkan)":
              return ""
            val = baris.get(pilihan_kolom)
            if pd.isna(val):
              return ""
            val_str = str(val).strip()
            if val_str.endswith(".0") and val_str[:-2].isdigit():
              val_str = val_str[:-2]
            return "" if val_str.lower() == "nan" else val_str

          for _, r in df_up.iterrows():
            nama_val = ambil_nilai_terpilih(r, kolom_nama)
            if not nama_val:
              continue

            if lewati_duplikat and nama_val.lower() in existing_names:
              jumlah_dilewati += 1
              continue

            existing_names.add(nama_val.lower())

            records_to_insert.append({
                "nama_perusahaan": nama_val,
                "nib": "",
                "alamat": ambil_nilai_terpilih(r, kolom_alamat),
                "no_telp": ambil_nilai_terpilih(r, kolom_telp),
                "email": ambil_nilai_terpilih(r, kolom_email),
                "jumlah_pekerja": 0,
                "pp": "Tidak Ada",
                "pkb": "Tidak Ada",
                "lks_bipartit": "Tidak Ada",
                "sp_sb": "Tidak Ada",
                "bpjs": "Belum",
                "perselisihan": "",
                "phk": "",
                "pembinaan": "",
                "status": "Aktif",
            })

          if records_to_insert:
            batch_size = 200
            for i in range(0, len(records_to_insert), batch_size):
              supabase.table("tabel_perusahaan").insert(
                  records_to_insert[i : i + batch_size]
              ).execute()

            pesan = (
                f"Berhasil mengimpor **{len(records_to_insert):,}**"
                " perusahaan baru ke database!"
            )
            if jumlah_dilewati > 0:
              pesan += f" ({jumlah_dilewati:,} data duplikat dilewati)."
            st.success(pesan)
            st.rerun()
          else:
            st.warning(
                "Tidak ada data baru yang diimpor (semua baris kosong atau"
                " sudah ada di database)."
            )

    except Exception as e:
      st.error(f"Terjadi kesalahan saat membaca/mengimpor file Excel: {e}")

# ==========================================
# TAB 4: EDIT DATA PERUSAHAAN (VIA DROPDOWN)
# ==========================================
with tab4:
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

      ec3, ec4 = st.columns(2)
      u_telp = ec3.text_input(
          "Nomor Telepon", value=safe_str(row_edit.get("no_telp", ""))
      )
      u_email = ec4.text_input(
          "Email Perusahaan", value=safe_str(row_edit.get("email", ""))
      )

      ec5, ec6 = st.columns([2, 1])
      u_alamat = ec5.text_area("Alamat", value=safe_str(row_edit["alamat"]))
      u_pekerja = ec6.number_input(
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
      bpjs_tab4_awal = normalisasi_bpjs(row_edit.get("bpjs", "Belum"))
      u_bpjs = ek5.selectbox(
          "BPJS",
          opsi_bpjs,
          index=opsi_bpjs.index(bpjs_tab4_awal),
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
                "no_telp": u_telp.strip(),
                "email": u_email.strip(),
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
# TAB 5: HAPUS DATA PERUSAHAAN
# ==========================================
with tab5:
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

# ==========================================
# TAB 6: CEK & BERSIHKAN NAMA PERUSAHAAN DOBEL
# ==========================================
with tab6:
  st.subheader("Pengecekan Nama Perusahaan Ganda (Duplikat)")

  if not df_raw.empty and "nama_perusahaan" in df_raw.columns:
    df_cek = df_raw.copy()
    df_cek["nama_norm"] = (
        df_cek["nama_perusahaan"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )

    duplikat_mask = df_cek.duplicated(subset=["nama_norm"], keep=False) & (
        df_cek["nama_norm"] != ""
    )
    df_dobel = df_cek[duplikat_mask].sort_values(
        by=["nama_norm", "id"], ascending=[True, True]
    )

    if df_dobel.empty:
      st.success("✅ Tidak ditemukan nama perusahaan yang dobel di database.")
    else:
      jml_kelompok = df_dobel["nama_norm"].nunique()
      st.warning(
          f"⚠️ Ditemukan **{jml_kelompok}** nama perusahaan yang ganda"
          f" (total **{len(df_dobel)}** baris data). Periksa detail di bawah"
          " sebelum menghapus baris duplikat."
      )

      kolom_tampil_dobel = [
          "id",
          "nama_perusahaan",
          "nib",
          "alamat",
          "no_telp",
          "jumlah_pekerja",
          "pp",
          "pkb",
          "lks_bipartit",
          "bpjs",
          "status",
      ]
      kolom_ada = [c for c in kolom_tampil_dobel if c in df_dobel.columns]
      st.dataframe(
          df_dobel[kolom_ada],
          use_container_width=True,
          hide_index=True,
      )

      st.markdown("---")
      st.markdown("**Hapus Baris Duplikat Tertentu:**")

      opsi_hapus_dobel = {
          f"ID {row['id']} | {row['nama_perusahaan']} (NIB: {row.get('nib') or '-'}, Pekerja: {row.get('jumlah_pekerja') or 0}, PP: {row.get('pp') or '-'})": (
              row["id"]
          )
          for _, row in df_dobel.iterrows()
      }

      pilih_dobel_hapus = st.selectbox(
          "Pilih baris duplikat yang ingin dihapus (sisakan 1 data yang paling"
          " lengkap):",
          list(opsi_hapus_dobel.keys()),
          key="select_hapus_duplikat",
      )

      if st.button(
          "🗑️ Hapus Baris Duplikat Terpilih",
          type="primary",
          key="btn_hapus_duplikat",
      ):
        try:
          id_del = opsi_hapus_dobel[pilih_dobel_hapus]
          supabase.table("tabel_perusahaan").delete().eq("id", id_del).execute()
          st.success(f"Baris duplikat (ID {id_del}) berhasil dihapus!")
          st.rerun()
        except Exception as e:
          st.error(f"Gagal menghapus data duplikat: {e}")
  else:
    st.info("Belum ada data perusahaan di database.")
