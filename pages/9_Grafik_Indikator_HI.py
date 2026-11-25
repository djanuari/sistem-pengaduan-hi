import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import Client, create_client
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning(
      "⚠️ Anda belum login. Silakan kembali ke halaman utama untuk login."
  )
  st.stop()

st.set_page_config(
    page_title="Dashboard Grafik Indikator HI", page_icon="📊", layout="wide"
)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("📊 Dashboard Capaian Indikator Hubungan Industrial")
st.markdown("---")


def fetch_all_rows(
    table_name: str, order_col: str | None = None
) -> pd.DataFrame:
  all_data = []
  batch_size = 1000
  offset = 0
  while True:
    query = supabase.table(table_name).select("*")
    if order_col:
      query = query.order(order_col, desc=False)
    res = query.range(offset, offset + batch_size - 1).execute()
    batch = res.data or []
    all_data.extend(batch)
    if len(batch) < batch_size:
      break
    offset += batch_size
  return pd.DataFrame(all_data)


def load_all_data():
  df_perusahaan = pd.DataFrame()
  df_pengaduan = pd.DataFrame()
  try:
    df_perusahaan = fetch_all_rows("tabel_perusahaan", order_col="id")
  except Exception as e:
    st.error(f"Gagal memuat tabel_perusahaan: {e}")

  try:
    df_pengaduan = fetch_all_rows("tabel_pengaduan", order_col=None)
  except Exception as e:
    st.error(f"Gagal memuat tabel_pengaduan: {e}")

  return df_perusahaan, df_pengaduan


df_perusahaan, df_pengaduan = load_all_data()

# ==========================================
# FILTER DATA (TERMASUK TAHUN 2020 - 2035)
# ==========================================
with st.expander("🔍 Filter Data Tampilan", expanded=True):
  f_col1, f_col2 = st.columns(2)

  status_perusahaan_opsi = ["Semua Status Perusahaan"]
  if not df_perusahaan.empty and "status" in df_perusahaan.columns:
    status_perusahaan_opsi += sorted(
        df_perusahaan["status"].dropna().unique().tolist()
    )
  pilih_status_p = f_col1.selectbox(
      "Filter Status Perusahaan (Indikator Perusahaan):",
      status_perusahaan_opsi,
  )

  tahun_opsi = ["Semua Tahun"] + [str(t) for t in range(2020, 2036)]
  if not df_pengaduan.empty and "tanggal_masuk" in df_pengaduan.columns:
    df_pengaduan["tahun"] = pd.to_datetime(
        df_pengaduan["tanggal_masuk"], errors="coerce"
    ).dt.year

  pilih_tahun = f_col2.selectbox(
      "Filter Tahun Pengaduan (Indikator Perselisihan):", tahun_opsi
  )

df_p_filtered = df_perusahaan.copy()
if (
    not df_p_filtered.empty
    and pilih_status_p != "Semua Status Perusahaan"
    and "status" in df_p_filtered.columns
):
  df_p_filtered = df_p_filtered[df_p_filtered["status"] == pilih_status_p]

df_k_filtered = df_pengaduan.copy()
if not df_k_filtered.empty and pilih_tahun != "Semua Tahun":
  if "tahun" in df_k_filtered.columns:
    df_k_filtered = df_k_filtered[df_k_filtered["tahun"] == int(pilih_tahun)]
  else:
    df_k_filtered = df_k_filtered.iloc[0:0]

# ==========================================
# HITUNG 6 INDIKATOR UTAMA (TERMASUK BPJS)
# ==========================================
total_perusahaan = len(df_p_filtered)

if total_perusahaan > 0:
  jml_pp = int((df_p_filtered["pp"] == "Ada").sum())
  persen_pp = (jml_pp / total_perusahaan) * 100

  jml_pkb = int((df_p_filtered["pkb"] == "Ada").sum())
  persen_pkb = (jml_pkb / total_perusahaan) * 100

  jml_lks = int((df_p_filtered["lks_bipartit"] == "Ada").sum())
  persen_lks = (jml_lks / total_perusahaan) * 100

  pembinaan_bersih = (
      df_p_filtered["pembinaan"].fillna("").astype(str).str.strip()
  )
  jml_pembinaan = int(((pembinaan_bersih != "") & (pembinaan_bersih != "-")).sum())
  persen_pembinaan = (jml_pembinaan / total_perusahaan) * 100

  # Indikator BPJS
  if "bpjs" in df_p_filtered.columns:
    bpjs_series = df_p_filtered["bpjs"].fillna("").astype(str).str.strip()
    jml_bpjs_lengkap = int(
        (bpjs_series == "Terdaftar Lengkap (Kesehatan & TK)").sum()
    )
    jml_bpjs_sebagian = int((bpjs_series == "Sebagian").sum())
    jml_bpjs_terdaftar = jml_bpjs_lengkap + jml_bpjs_sebagian
    jml_bpjs_belum = max(total_perusahaan - jml_bpjs_terdaftar, 0)
  else:
    jml_bpjs_lengkap = jml_bpjs_sebagian = jml_bpjs_terdaftar = 0
    jml_bpjs_belum = total_perusahaan

  persen_bpjs = (jml_bpjs_terdaftar / total_perusahaan) * 100
else:
  jml_pp = jml_pkb = jml_lks = jml_pembinaan = 0
  jml_bpjs_lengkap = jml_bpjs_sebagian = jml_bpjs_terdaftar = jml_bpjs_belum = 0
  persen_pp = persen_pkb = persen_lks = persen_pembinaan = persen_bpjs = 0.0

total_perselisihan = len(df_k_filtered)
if total_perselisihan > 0 and "status" in df_k_filtered.columns:
  jml_selesai = int((df_k_filtered["status"] == "Selesai").sum())
  persen_selesai = (jml_selesai / total_perselisihan) * 100
else:
  jml_selesai = 0
  persen_selesai = 0.0

# ==========================================
# RINGKASAN KARTU KPI (6 INDIKATOR)
# ==========================================
st.subheader("Ringkasan Capaian Indikator")
m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.metric(
    label="1. Memiliki PP",
    value=f"{persen_pp:.1f}%",
    delta=f"{jml_pp:,} / {total_perusahaan:,}",
    delta_color="off",
)
m2.metric(
    label="2. Memiliki PKB",
    value=f"{persen_pkb:.1f}%",
    delta=f"{jml_pkb:,} / {total_perusahaan:,}",
    delta_color="off",
)
m3.metric(
    label="3. LKS Bipartit",
    value=f"{persen_lks:.1f}%",
    delta=f"{jml_lks:,} / {total_perusahaan:,}",
    delta_color="off",
)
m4.metric(
    label="4. Kasus Selesai",
    value=f"{persen_selesai:.1f}%",
    delta=f"{jml_selesai:,} / {total_perselisihan:,}",
    delta_color="off",
)
m5.metric(
    label="5. Pembinaan HI",
    value=f"{persen_pembinaan:.1f}%",
    delta=f"{jml_pembinaan:,} / {total_perusahaan:,}",
    delta_color="off",
)
m6.metric(
    label="6. Terdaftar BPJS",
    value=f"{persen_bpjs:.1f}%",
    delta=f"{jml_bpjs_terdaftar:,} / {total_perusahaan:,}",
    delta_color="off",
)

st.markdown("---")

# ==========================================
# GRAFIK PERBANDINGAN 6 INDIKATOR (BAR CHART)
# ==========================================
st.subheader("Grafik Perbandingan Persentase Indikator")

df_ringkasan = pd.DataFrame({
    "Indikator": [
        "1. Memiliki PP",
        "2. Memiliki PKB",
        "3. Memiliki LKS Bipartit",
        "4. Perselisihan Selesai",
        "5. Mendapat Pembinaan HI",
        "6. Terdaftar BPJS",
    ],
    "Persentase (%)": [
        round(persen_pp, 2),
        round(persen_pkb, 2),
        round(persen_lks, 2),
        round(persen_selesai, 2),
        round(persen_pembinaan, 2),
        round(persen_bpjs, 2),
    ],
    "Keterangan": [
        f"{jml_pp:,} / {total_perusahaan:,} Perusahaan",
        f"{jml_pkb:,} / {total_perusahaan:,} Perusahaan",
        f"{jml_lks:,} / {total_perusahaan:,} Perusahaan",
        f"{jml_selesai:,} / {total_perselisihan:,} Kasus",
        f"{jml_pembinaan:,} / {total_perusahaan:,} Perusahaan",
        (
            f"{jml_bpjs_terdaftar:,} / {total_perusahaan:,} Perusahaan"
            f" (Lengkap: {jml_bpjs_lengkap:,}, Sebagian: {jml_bpjs_sebagian:,})"
        ),
    ],
})

fig_bar = px.bar(
    df_ringkasan,
    x="Indikator",
    y="Persentase (%)",
    text="Persentase (%)",
    hover_data=["Keterangan"],
    color="Indikator",
    color_discrete_sequence=[
        "#1f77b4",
        "#2ca02c",
        "#ff7f0e",
        "#9467bd",
        "#17becf",
        "#e377c2",
    ],
)
fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_bar.update_layout(
    yaxis=dict(range=[0, 115], title="Persentase (%)"),
    xaxis=dict(title=""),
    showlegend=False,
    height=420,
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ==========================================
# GRAFIK RINCIAN MASING-MASING INDIKATOR (DONUT)
# ==========================================
st.subheader("Rincian Proporsi Masing-Masing Indikator")


def buat_donut(judul, names_list, values_list, color_map):
  if sum(values_list) == 0:
    fig = go.Figure()
    fig.add_annotation(
        text="Belum ada data", x=0.5, y=0.5, showarrow=False, font_size=14
    )
    fig.update_layout(
        title=judul,
        height=300,
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig

  fig = px.pie(
      names=names_list,
      values=values_list,
      hole=0.55,
      color=names_list,
      color_discrete_map=color_map,
  )
  fig.update_traces(textinfo="percent+value", textposition="inside")
  fig.update_layout(
      title=dict(text=judul, font=dict(size=14)),
      legend=dict(
          orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5
      ),
      margin=dict(t=45, b=45, l=10, r=10),
      height=330,
  )
  return fig


# Baris 1: Indikator 1, 2, 3
c1, c2, c3 = st.columns(3)
with c1:
  st.plotly_chart(
      buat_donut(
          "Indikator 1: Peraturan Perusahaan (PP)",
          ["Memiliki PP", "Belum / Proses"],
          [jml_pp, max(total_perusahaan - jml_pp, 0)],
          {"Memiliki PP": "#1f77b4", "Belum / Proses": "#e0e0e0"},
      ),
      use_container_width=True,
  )
with c2:
  st.plotly_chart(
      buat_donut(
          "Indikator 2: Perjanjian Kerja Bersama (PKB)",
          ["Memiliki PKB", "Belum / Proses"],
          [jml_pkb, max(total_perusahaan - jml_pkb, 0)],
          {"Memiliki PKB": "#2ca02c", "Belum / Proses": "#e0e0e0"},
      ),
      use_container_width=True,
  )
with c3:
  st.plotly_chart(
      buat_donut(
          "Indikator 3: LKS Bipartit",
          ["Memiliki LKS Bipartit", "Belum / Proses"],
          [jml_lks, max(total_perusahaan - jml_lks, 0)],
          {"Memiliki LKS Bipartit": "#ff7f0e", "Belum / Proses": "#e0e0e0"},
      ),
      use_container_width=True,
  )

# Baris 2: Indikator 4, 5, 6 (BPJS)
c4, c5, c6 = st.columns(3)
with c4:
  st.plotly_chart(
      buat_donut(
          "Indikator 4: Penyelesaian Perselisihan HI",
          ["Selesai", "Dalam Proses / Belum"],
          [jml_selesai, max(total_perselisihan - jml_selesai, 0)],
          {"Selesai": "#9467bd", "Dalam Proses / Belum": "#e0e0e0"},
      ),
      use_container_width=True,
  )
with c5:
  st.plotly_chart(
      buat_donut(
          "Indikator 5: Pembinaan Hubungan Industrial",
          ["Sudah Dibina", "Belum Dibina"],
          [jml_pembinaan, max(total_perusahaan - jml_pembinaan, 0)],
          {"Sudah Dibina": "#17becf", "Belum Dibina": "#e0e0e0"},
      ),
      use_container_width=True,
  )
with c6:
  st.plotly_chart(
      buat_donut(
          "Indikator 6: Kepesertaan BPJS",
          ["Terdaftar Lengkap", "Sebagian", "Belum Terdaftar"],
          [jml_bpjs_lengkap, jml_bpjs_sebagian, jml_bpjs_belum],
          {
              "Terdaftar Lengkap": "#e377c2",
              "Sebagian": "#f7b6d2",
              "Belum Terdaftar": "#e0e0e0",
          },
      ),
      use_container_width=True,
  )
