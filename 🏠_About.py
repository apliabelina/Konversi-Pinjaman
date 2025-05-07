import streamlit as st

# Judul utama
st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Dashboard Analisis Konversi Pinjaman")
st.markdown("""
Selamat datang di **Dashboard Analisis Konversi Pinjaman**.  
Dashboard ini menyajikan tiga fitur utama untuk mendukung analisis dan pengambilan keputusan.
""")

st.markdown("---")

# Tiga kolom
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background-color:#C4DCFF; padding:20px; border-radius:10px">
        <h3>📈 Monitoring Data Market</h3>
        <p>Pantau <b>pergerakan nilai tukar</b>, <b>interest rate global</b>, <b>yield surat berharga</b>, dan <b>suku bunga bank sentral</b>.</p>
        <p>Halaman ini membantu memahami dinamika pasar yang memengaruhi strategi pengelolaan utang.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background-color:#EBCEFF; padding:20px; border-radius:10px">
        <h3>🔁 Monitoring Hasil Konversi</h3>
        <p>Tinjau <b>realisasi transaksi konversi pinjaman</b> yang telah dilakukan, lengkap dengan nilai dan status terkini.</p>
        <p>Membantu melacak efektivitas konversi dan evaluasi strategis keuangan.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background-color:#FFDFBD; padding:20px; border-radius:10px">
        <h3>📅 Proyeksi Kewajiban Utang</h3>
        <p>Lihat <b>proyeksi pembayaran utang</b> (pokok dan bunga) untuk periode mendatang.</p>
        <p>Mendukung <i>cash planning</i> dan mitigasi risiko pembiayaan.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="background-color:#f2f2f2; padding:15px; border-radius:8px; border-left: 6px solid #808080;">
    ℹ️ <b>Gunakan menu di sidebar kiri</b> untuk mulai menjelajahi halaman-halaman di atas.
</div>
""", unsafe_allow_html=True)