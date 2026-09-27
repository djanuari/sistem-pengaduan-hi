import streamlit as st

st.set_page_config(
    page_title="Sistem Pengaduan Hubungan Industrial",
    page_icon="⚖️",
    layout="wide",
)

# Inisialisasi status sesi login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- TAMPILAN JIKA BELUM LOGIN (LANDING PAGE) ---
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 30px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #2c3e50;'>🔐 Login Admin</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #7f8c8d;'>Sistem Informasi Pengaduan HI</p>", unsafe_allow_html=True)
        
        with st.form("form_login_utama"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk Aplikasi", use_container_width=True)
            
            if submit:
                # Ganti username & password sesuai keinginan Anda di sini
                if username == "admin" and password == "12345":
                    st.session_state.logged_in = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
                    
    st.stop() # Menghentikan halaman agar menu sidebar tidak muncul sebelum login

# --- TAMPILAN SETELAH BERHASIL LOGIN (BERANDA) ---
st.title("⚖️ Selamat Datang di Sistem Informasi Pengaduan HI")
st.markdown("---")

st.success("Anda berhasil masuk sebagai Administrator.")

st.info("""
    ### 📂 Petunjuk Navigasi Menu:
    Silakan pilih menu di **sidebar (sebelah kiri)** untuk mengakses fitur berikut:
    * **Summary Report**: Melihat laporan keseluruhan, ekspor data ke Excel, dan unduh PDF detail berdasarkan ID.
    * **1 Input Data**: Mengisi form pengaduan baru, memperbarui data, atau menghapus data.
    * **2 Dashboard Grafik**: Melihat rekam jejak statistik, filter berdasarkan tahun/bulan, dan grafik lingkaran.
""")

st.markdown("---")
if st.button("🚪 Keluar (Logout)", type="secondary"):
    st.session_state.logged_in = False
    st.rerun()
