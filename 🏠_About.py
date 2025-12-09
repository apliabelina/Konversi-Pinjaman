import streamlit as st

# Judul utama
st.set_page_config(page_title="Dashboard", layout="wide",initial_sidebar_state="expanded",page_icon="📊")

st.markdown("""
    <style>
    /* Warna latar sidebar */
    section[data-testid="stSidebar"] {
        background-color: #100E34;
    }

    /* Menu aktif */
    [data-testid="stSidebar"] a[aria-current="page"] {
        background-color: #FFBF18;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        display: block;
        text-decoration: none;
    }

    /* Teks menu aktif */
    [data-testid="stSidebar"] a[aria-current="page"] span {
        color: #262730 !important;
        font-weight: bold !important;
    }

    /* Menu tidak aktif (link) */
    [data-testid="stSidebar"] a:not([aria-current="page"]) {
        color: #ffffff !important;
        text-decoration: none;
    }

    /* Teks menu tidak aktif */
    [data-testid="stSidebar"] a:not([aria-current="page"]) span {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* Hover efek */
    [data-testid="stSidebar"] a:hover span {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)


#st.write(st.runtime.scriptrunner.get_script_run_ctx())
st.title("Dashboard Analisis Konversi Pinjaman")

# ==== Credential ====
USER_CREDENTIALS = {
    "ARP": "1234",
    "Peserta": "123456"
}

def login():
    with st.container():
        left, right = st.columns([7,5], gap="large")
        with left:
            st.markdown("""
                Selamat datang 👋.  
                """)

            # Layout login card
            with st.container():
                st.markdown("---")
                st.markdown("""
                    <div style="background-color:#100E34; padding:10px; border-radius:5px">
                        <h3 style="color: white;">Login</h3>
                        <p style="color: white;">Silakan login untuk mengakses dashboard</p>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")
                username  = st.text_input("Username")
                password  = st.text_input("Password", type="password")
                login_btn = st.button("Login")

                st.markdown('</div></div>', unsafe_allow_html=True)
                
            if login_btn:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.session_state["authenticated"] = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

            st.markdown("""
                <div style="text-align:right;">
                    <a href="#" style="font-size: 12px;">Lupa password?</a>
                </div>               
                </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            
        with right:
            st.markdown('<div class="card">', unsafe_allow_html=True)
           # HERE = Path(__file__).parent  # folder tempat file .py ini berada
           # img_path = HERE / "Halaman" / "pic1.png"
            
            st.image("\mount\src\konversi-pinjaman\Halaman\pic1.png")

            st.markdown('</div>', unsafe_allow_html=True)

    st.write("")  # spacing



# ==== Logout Button ====
def logout():
    with st.container():
        col1, col2 = st.columns([8, 2])
        with col2:
            if st.button("🚪 Logout"):
                st.session_state["authenticated"] = False
                st.rerun()

# ==== Autentikasi ====
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
else:
    logout()
    cola, colb = st.columns([8, 2])
    with cola:
        st.markdown("""
                Selamat Bekerja 👋.  
                """)
    with colb:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image("Halaman\pic1.png")

        st.markdown('</div>', unsafe_allow_html=True)
    #st.write("Gunakan menu di sidebar untuk mengakses halaman lain.")




