import datetime
import io
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
opsi_bpjs = [
    "Terdaftar Lengkap (Kesehatan & TK)",
    "Sebagian",
    "Belum Terdaftar",
]
opsi_status = ["Aktif", "Tidak Aktif", "Dalam Pengawasan / Pembinaan"]


def safe_str(val):
  return str(val) if val is not None and str(val) != "None" else ""


# Fungsi Pembuat PDF Landscape A4 (16 Kolom)
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
      f"Dicetak pada: {tgl_cetak} | Total Perusahaan: {len(df)}",
      ln=True,
      align="C",
  )
  pdf.ln(4)

  # Total lebar = 277 mm (pas untuk kertas A4 Landscape margin 10mm)
  col_widths = [
      7,
      26,
      17,
      24,
      18,
      22,
      11,
      12,
      12,
      14,
      12,
      19,
      20,
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
        str(row["Nama Perusahaan"])[:22],
        str(row["NIB"])[:13],
        str(row["Alamat"])[:20],
        str(row["No. Telepon"])[:14],
        str(row["Email"])[:18],
        str(row["Jumlah Pekerja"]),
        str(row["PP"])[:9],
        str(row["PKB"])[:9],
        str(row["LKS Bipartit"])[:9],
        str(row["SP/SB"])[:9],
        str(row["BPJS"])[:14],
        str(row["Perselisihan"])[:16],
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
        "L",
        "L",
        "L",
        "L",
        "C",
    ]
    for w, val, al in zip(col_widths, row_vals, aligns):
      pdf.cell(w, 6, val, border=1, align=al, fill=fill)
    pdf.ln()

  return bytes(pdf.output())


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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Daftar Perusahaan",
    "➕ Tambah Perusahaan",
    "📤 Impor Excel",
    "✏️ Edit Data",
    "🗑️ Hapus Data",
])

# ==========================================
# TAB 1: DAFTAR PERUSAHAAN & EKSPOR (EXCEL, CSV, PDF)
# ==========================================
with tab1:
  st.subheader("Rekapitulasi Data Perusahaan")

  if not df_raw.empty:
    # Pastikan kolom baru ada meskipun data lama bernilai null
    for col_cek in ["no_telp", "email"]:
      if col_cek not in df_raw.columns:
        df_raw[col_cek] = ""

    c_cari1, c_cari2 = st.columns([2, 1])
    kata_kunci = c_cari1.text_input(
        "🔍 Cari Nama Perusahaan / NIB / Alamat / Email / No. Telepon:", ""
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
          | df_tampil["no_telp"].fillna("").str.contains(kata_kunci, case=False)
          | df_tampil["email"].fillna("").str.contains(kata_kunci, case=False)
      )
      df_tampil = df_tampil[mask]

    if filter_status != "Semua":
      df_tampil = df_tampil[df_tampil["status"] == filter_status]

    df_tampil = df_tampil.reset_index(drop=True)
    df_tampil.insert(0, "No", range(1, len(df_tampil) + 1))

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

    st.dataframe(df_final, use_container_width=True, hide_index=True)

    st.caption(
        f"Total ditampilkan: **{len(df_final)}** perusahaan | Total pekerja:"
        f" **{int(df_final['Jumlah Pekerja'].fillna(0).sum()):,}** orang"
    )

    st.markdown("**Ekspor Data Terfilter:**")
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
      df_final.to_excel(writer, index=False, sheet_name="Data_Perusahaan")

    col_dl1.download_button(
        label="📗 Unduh Excel (.xlsx)",
        data=buffer_excel.getvalue(),
        file_name="Daftar_Perusahaan_HI.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    csv_data = df_final.to_csv(index=False).encode("utf-8-sig")
    col_dl2.download_button(
        label="📄 Unduh CSV (.csv)",
        data=csv_data,
        file_name="Daftar_Perusahaan_HI.csv",
        mime="text/csv",
        use_container_width=True,
    )

    pdf_bytes = generate_pdf_perusahaan(df_final)
    col_dl3.download_button(
        label="📕 Unduh PDF (.pdf)",
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
      "Anda dapat mengunggah file Excel (`.xlsx` / `.xls`) yang **hanya"
      " berisi kolom Nama Perusahaan saja**, atau sudah mencakup kolom"
      " **Alamat**, **No. Telepon**, dan **Email** sekaligus."
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
        st.write(f"Ditemukan **{len(df_up)}** baris data pada file:")
        st.dataframe(df_up.head(10), use_container_width=True)

        kolom_excel = list(df_up.columns)
        default_idx = 0
        for i, col in enumerate(kolom_excel):
          if "nama" in str(col).lower() or "perusahaan" in str(col).lower():
            default_idx = i
            break

        kolom_nama = st.selectbox(
            "Pilih kolom di Excel yang berisi Nama Perusahaan:",
            kolom_excel,
            index=default_idx,
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

          for _, r in df_up.iterrows():
            nama_val = str(r.get(kolom_nama, "")).strip()
            if not nama_val or nama_val.lower() == "nan":
              continue

            if lewati_duplikat and nama_val.lower() in existing_names:
              jumlah_dilewati += 1
              continue

            existing_names.add(nama_val.lower())

            def ambil_kolom(kandidat_nama, default_val=""):
              for c in df_up.columns:
                if str(c).strip().lower() in kandidat_nama:
                  val = r.get(c)
                  if pd.notna(val) and str(val).strip() != "":
                    return str(val).strip()
              return default_val

            pekerja_str = ambil_kolom(
                ["jumlah pekerja", "pekerja", "jumlah_pekerja"], "0"
            )
            try:
              jml_pekerja_int = int(float(pekerja_str))
            except ValueError:
              jml_pekerja_int = 0

            records_to_insert.append({
                "nama_perusahaan": nama_val,
                "nib": ambil_kolom(["nib"], ""),
                "alamat": ambil_kolom(["alamat", "address"], ""),
                "no_telp": ambil_kolom(
                    [
                        "no. telepon",
                        "no telepon",
                        "nomor telepon",
                        "telepon",
                        "telp",
                        "no_telp",
                        "hp",
                        "kontak",
                    ],
                    "",
                ),
                "email": ambil_kolom(["email", "e-mail", "surel"], ""),
                "jumlah_pekerja": jml_pekerja_int,
                "pp": ambil_kolom(["pp"], "Tidak Ada"),
                "pkb": ambil_kolom(["pkb"], "Tidak Ada"),
                "lks_bipartit": ambil_kolom(
                    ["lks bipartit", "lks_bipartit", "lks"], "Tidak Ada"
                ),
                "sp_sb": ambil_kolom(["sp/sb", "sp_sb", "sp", "sb"], "Tidak Ada"),
                "bpjs": ambil_kolom(["bpjs"], "Belum Terdaftar"),
                "perselisihan": ambil_kolom(["perselisihan"], ""),
                "phk": ambil_kolom(["phk"], ""),
                "pembinaan": ambil_kolom(["pembinaan"], ""),
                "status": ambil_kolom(["status"], "Aktif"),
            })

          if records_to_insert:
            batch_size = 200
            for i in range(0, len(records_to_insert), batch_size):
              supabase.table("tabel_perusahaan").insert(
                  records_to_insert[i : i + batch_size]
              ).execute()

            pesan = (
                f"Berhasil mengimpor **{len(records_to_insert)}** perusahaan"
                " baru ke database!"
            )
            if jumlah_dilewati > 0:
              pesan += f" ({jumlah_dilewati} data duplikat dilewati)."
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
# TAB 4: EDIT DATA PERUSAHAAN
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
