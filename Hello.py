import streamlit as st

# ==============================
# CONFIG HALAMAN
# ==============================
st.set_page_config(
    page_title="JIAT Smart Studio",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# HEADER & SAMBUTAN
# ==============================
st.title("🏗️ JIAT Smart Studio")
st.subheader("Integrated Construction Cost Estimator System")
st.markdown("---")

# Pesan Sambutan
st.markdown("""
### Selamat Datang di Super App Konstruksi
Aplikasi ini dirancang untuk mempermudah perhitungan **Rencana Anggaran Biaya (RAB)** lintas bidang secara terintegrasi, akurat, dan sesuai standar **AHSP 2025**.

Silakan pilih modul pekerjaan melalui **Menu di Sebelah Kiri (Sidebar)**.
""")

# ==============================
# CARD MODUL (Informasi Status)
# ==============================
st.write("")
st.write("### 📂 Modul Tersedia")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**1. SUMBER DAYA AIR (SDA)**")
    st.markdown("""
    - 🌊 Saluran Irigasi
    - 🧱 Bendung & Pintu Air
    - 🚜 Pengerukan Sungai
    - ✅ **Status: ACTIVE**
    """)

with col2:
    st.warning("**2. CIPTA KARYA (Gedung)**")
    st.markdown("""
    - 🏢 Struktur Beton
    - 🏠 Arsitektur & Finishing
    - 🔌 MEP (Mekanikal Elektrikal)
    - 🚧 **Status: COMING SOON**
    """)

with col3:
    st.warning("**3. BINA MARGA (Jalan)**")
    st.markdown("""
    - 🛣️ Jalan & Jembatan
    - 🚜 Aspal & Rigid Pavement
    - 🏗️ Drainase Jalan
    - 🚧 **Status: COMING SOON**
    """)

# ==============================
# FITUR UNGGULAN
# ==============================
st.markdown("---")
st.markdown("### 🚀 Fitur Unggulan Engine")
st.markdown("""
1.  **Auto-Detect Resource:** Otomatis membaca kebutuhan Tenaga, Bahan, dan Alat dari database.
2.  **Smart Parsing:** Mampu membaca format teks AHSP yang kompleks.
3.  **Multi-Standard:** Mendukung analisa SNI, PUPR, dan AHSP Daerah.
4.  **Audit-Ready:** Output format BOQ yang transparan dan mudah diperiksa.
""")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption("© 2026 JIAT Smart Studio | Developed with Python & Streamlit")
