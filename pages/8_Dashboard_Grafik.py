import pandas as pd
import plotly.express as px
from supabase import Client, create_client
import streamlit as st

st.set_page_config(
    page_title="Dashboard Grafik Pengaduan", page_icon="📈", layout="wide"
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("📈 Dashboard Grafik & Statistik Pengaduan (Cloud)")
st.markdown("---")

try:
  response = supabase.table("tabel_pengaduan").select("*").execute()
  df = pd.DataFrame(response.data)
except Exception as e:
  st.error(f"Gagal mengambil data dari Supabase: {e}")
  df = pd.DataFrame()

if not df.empty:
  df["tanggal_masuk_dt"] = pd.to_datetime(
      df["tanggal_masuk"], errors="coerce"
  )
  df["Tahun"] = (
      df["tanggal_masuk_dt"].dt.year.fillna(0).astype(int).astype(str)
  )

  bulan_dict = {
      1: "Januari",
      2: "Februari",
      3: "Maret",
      4: "April",
      5: "Mei",
      6: "Juni",
      7: "Juli",
      8: "Agustus",
      9: "September",
      10: "Oktober",
      11: "November",
      12: "Desember",
  }
  df["Bulan"] = df["tanggal_masuk_dt"].dt.month.map(bulan_dict)

  f1, f2 = st.columns(2)
  daftar_tahun = [str(y) for y in range(2020, 2031)]
  tahun_filter = f1.selectbox("Pilih Tahun:", ["Semua Tahun"] + daftar_tahun)

  daftar_bulan = [
      "Semua Bulan",
      "Januari",
      "Februari",
      "Maret",
      "April",
      "Mei",
      "Juni",
      "Juli",
      "Agustus",
      "September",
      "Oktober",
      "November",
      "Desember",
  ]
  bulan_filter = f2.selectbox("Pilih Bulan:", daftar_bulan)

  df_filtered = df.copy()
  if tahun_filter != "Semua Tahun":
    df_filtered = df_filtered[df_filtered["Tahun"] == tahun_filter]
  if bulan_filter != "Semua Bulan":
    df_filtered = df_filtered[df_filtered["Bulan"] == bulan_filter]

  st.markdown("---")

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Pengaduan (Terfilter)", len(df_filtered))
  col2.metric(
      "Selesai", len(df_filtered[df_filtered["status"] == "Selesai"])
  )
  col3.metric(
      "Dalam Proses", len(df_filtered[df_filtered["status"] != "Selesai"])
  )

  st.markdown("---")


  def render_grafik_dan_tabel(judul, series_data, nama_kolom_kategori):
    st.subheader(judul)
    if not series_data.empty:
      df_table = series_data.reset_index()
      df_table.columns = [nama_kolom_kategori, "Jumlah"]

      total_row = pd.DataFrame({
          nama_kolom_kategori: ["JUMLAH TOTAL"],
          "Jumlah": [df_table["Jumlah"].sum()],
      })
      df_table = pd.concat([df_table, total_row], ignore_index=True)

      col_g, col_t = st.columns([1.5, 1])
      with col_g:
        fig = px.pie(
            df_table[df_table[nama_kolom_kategori] != "JUMLAH TOTAL"],
            names=nama_kolom_kategori,
            values="Jumlah",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)
      with col_t:
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    else:
      st.info("Tidak ada data untuk ditampilkan.")


  if "kategori" in df_filtered.columns:
    render_grafik_dan_tabel(
        "Distribusi Kategori Pengaduan",
        df_filtered["kategori"].value_counts(),
        "Kategori",
    )

  st.markdown("---")

  if "status" in df_filtered.columns:
    render_grafik_dan_tabel(
        "Distribusi Status Penanganan",
        df_filtered["status"].value_counts(),
        "Status",
    )

  st.markdown("---")

  if "sa_pilihan" in df_filtered.columns:
    df_penyelesaian = df_filtered[
        df_filtered["sa_pilihan"].notna() & (df_filtered["sa_pilihan"] != "-")
    ]
    render_grafik_dan_tabel(
        "Distribusi Pilihan Penyelesaian (Jika Selesai)",
        df_penyelesaian["sa_pilihan"].value_counts(),
        "Penyelesaian",
    )

  st.markdown("---")

  if "Tahun" in df_filtered.columns:
    render_grafik_dan_tabel(
        "Distribusi Berdasarkan Tahun Masuk",
        df_filtered["Tahun"].value_counts(),
        "Tahun",
    )

else:
  st.info("Belum ada data pengaduan yang tersimpan di dalam database cloud.")
