import streamlit as st

# Judul utama
st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Dashboard Analisis Konversi Pinjaman")

st.write("Streamlit version:", st.__version__)

st.markdown("""
Selamat datang di **Dashboard Analisis Konversi Pinjaman**.  
Dashboard ini menyajikan tiga fitur utama untuk mendukung analisis dan pengambilan keputusan.
""")


import streamlit as st





# ==== Credential ====
USER_CREDENTIALS = {
    "ARP": "1234",
    "user1": "1234"
}

# ==== Custom Login Layout ====
def login():
    col1, col2, col3 = st.columns([2,0.5,2])  # kiri lebar untuk deskripsi

    with col1:
        st.markdown("---")
        st.markdown("""
            <style>
                .info-box {
                    background-color: #f2f2f2;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 6px solid #808080;
                    text-align: left;
                    font-size: 18px;
                    font-weight: bold;
                    color: #1f77b4;
                    animation: blink 1.5s infinite;
                }

                @keyframes blink {
                    0% { opacity: 1; }
                    50% { opacity: 0.6; }
                    100% { opacity: 1; }
                }
            </style>

            <div class="info-box">
                ⬅️ <b>Gunakan menu di sidebar kiri</b> untuk mulai menjelajahi halaman-halaman berikut :
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="background-color:#00537A; padding:20px; border-radius:10px">
            <h3 style="color: white;">📈 Monitoring Data Market</h3>
            <p style="color: white;">Pantau <b>pergerakan nilai tukar</b>, <b>interest rate global</b>, <b>yield surat berharga</b>, dan <b>suku bunga bank sentral</b>.</p>
            <p style="color: white;">Halaman ini membantu memahami dinamika pasar yang memengaruhi strategi pengelolaan utang.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("""
        <div style="background-color:#A8e8F9; padding:20px; border-radius:10px">
            <h3>🔁 Monitoring Hasil Konversi</h3>
            <p>Tinjau <b>realisasi transaksi konversi pinjaman</b> yang telah dilakukan, lengkap dengan nilai dan status terkini.</p>
            <p>Membantu melacak efektivitas konversi dan evaluasi strategis keuangan.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("""
        <div style="background-color:#F5A201; padding:20px; border-radius:10px">
            <h3>📅 Proyeksi Kewajiban Utang</h3>
            <p>Lihat <b>proyeksi pembayaran utang</b> (pokok dan bunga) untuk periode mendatang.</p>
            <p>Mendukung <i>cash planning</i> dan mitigasi risiko pembiayaan.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    with col3:
        st.markdown("""
            <style>
                .centered {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .login-box {
                    background-color: white;
                    padding: 30px;
                    border-radius: 20px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    width: 800px;
                }
                /* Membesarkan label input */
                label {
                    font-size: 18px !important;
                    font-weight: 600 !important;
                }
                /* Ubah warna background input */
                .stTextInput > div > div > input {
                    background-color: white !important;  /* biru terang */
                }
            </style>
        """, unsafe_allow_html=True)

        # Layout login card
        with st.container():
            st.markdown("---")
            st.markdown("""
                <div style="background-color:#013C58; padding:15px; border-radius:5px">
                    <h3 style="color: white;">Login</h3>
                    <p style="color: white;">Silakan login untuk mengakses dashboard</p>
                </div>
                """, unsafe_allow_html=True)
            #st.markdown('<div class="centered"><div class="login-box">', 
                        #unsafe_allow_html=True)
           # st.markdown("### Login")
            #st.markdown('<p style="color: gray;">Silakan login untuk mengakses dashboard</p>', unsafe_allow_html=True)

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.button("Login")

            st.markdown('</div></div>', unsafe_allow_html=True)
            
        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["authenticated"] = True
                st.success("Login berhasil!")
                st.experimental_rerun()
            else:
                st.error("Username atau password salah.")

        st.markdown("""
            <div style="text-align:right;">
                <a href="#" style="font-size: 12px;">Lupa password?</a>
            </div>
            <br>
            <div style="text-align:center; font-size: 13px;">
                Belum punya akun? <a href="#">Daftar</a>
            </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
# ==== Logout Button ====
def logout():
    with st.container():
        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button("🚪 Logout"):
                st.session_state["authenticated"] = False
                st.experimental_rerun()

# ==== Autentikasi ====
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
else:
    logout()
    st.title("🎉 Selamat datang!")
    #st.write("Gunakan menu di sidebar untuk mengakses halaman lain.")
