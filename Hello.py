import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. CONFIG HALAMAN
# ==========================================
st.set_page_config(
    page_title="JIAT Smart Studio",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. INTELLIGENT DATA LOADER
# ==========================================
@st.cache_data
def cek_status_database():
    """
    Mendeteksi bidang apa saja yang SUDAH tersedia di file Excel Master.
    Return: List bidang yang aktif (misal: ['SDA', 'BM']) dan total item.
    """
    path = "data/db_ahsp_master.xlsx"
    stats = {
        "SDA": {"status": False, "count": 0},
        "BM":  {"status": False, "count": 0}, # Bina Marga
        "CK":  {"status": False, "count": 0}  # Cipta Karya
    }
    
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, sheet_name="master_ahsp")
            # Pastikan nama kolom kecil semua
            df.columns = df.columns.str.lower().str.strip()
            
            # Cek ketersediaan data
            if 'bidang' in df.columns:
                counts = df['bidang'].value_counts()
                for bidang in stats.keys():
                    if bidang in counts:
                        stats[bidang]["status"] = True
                        stats[bidang]["count"] = counts[bidang]
        except Exception:
            pass # Jika error, anggap semua belum aktif
            
    return stats

# Jalankan Pengecekan
db_stats = cek_status_database()

# ==========================================
# 3. HEADER & DASHBOARD
# ==========================================
st.title("🏗️ JIAT Smart Studio")
st.caption(f"Integrated Construction Cost Estimator System | AHSP 2025 Ready")
st.markdown("---")

# Pesan Sambutan
st.markdown("""
### Selamat Datang di Super App Konstruksi
Aplikasi ini mendeteksi database **AHSP 2025** secara *real-time*. 
Silakan pilih modul pekerjaan yang **AKTIF** di bawah ini atau melalui Sidebar.
""")

st.write("")
st.write("### 📂 Status Modul Terkini")

# Layout 3 Kolom
col1, col2, col3 = st.columns(3)

# --- FUNGSI PEMBANTU UNTUK KARTU ---
def render_card(container, title, code, icon, desc, items_tersedia):
    status_aktif = db_stats[code]["status"]
    jumlah_data = db_stats[code]["count"]
    
    with container:
        # Tampilkan Status (Hijau jika ada data, Kuning jika kosong)
        if status_aktif:
            st.success(f"**{title}**")
            st.markdown(f"✅ **ACTIVE** ({jumlah_data} Analisa)")
        else:
            st.warning(f"**{title}**")
            st.markdown("🚧 **COMING SOON** (Data Belum Diinput)")
            
        st.markdown(desc)
        
        # Tombol Navigasi (Hanya visual, navigasi tetap via Sidebar di MPA Streamlit)
        if status_aktif:
            st.button(f"Buka {code} ➡️", key=f"btn_{code}", disabled=False)
        else:
            st.button(f"Menunggu Data 🔒", key=f"btn_{code}", disabled=True)

# --- RENDER KARTU ---

# 1. SDA
render_card(
    col1, 
    "1. SUMBER DAYA AIR (SDA)", 
    "SDA", 
    "🌊", 
    """
    - 🌊 Saluran Irigasi
    - 🧱 Bendung & Pintu Air
    - 🚜 Pengerukan Sungai
    """,
    items_tersedia=db_stats["SDA"]["count"]
)

# 2. CIPTA KARYA
render_card(
    col2, 
    "2. CIPTA KARYA (Gedung)", 
    "CK", 
    "🏢", 
    """
    - 🏢 Struktur Beton & Baja
    - 🏠 Arsitektur & Finishing
    - 🔌 MEP (Mekanikal Elektrikal)
    """,
    items_tersedia=db_stats["CK"]["count"]
)

# 3. BINA MARGA
render_card(
    col3, 
    "3. BINA MARGA (Jalan)", 
    "BM", 
    "🛣️", 
    """
    - 🛣️ Jalan & Jembatan
    - 🚜 Aspal & Rigid Pavement
    - 🏗️ Drainase Jalan
    """,
    items_tersedia=db_stats["BM"]["count"]
)

# ==========================================
# 4. FOOTER STATISTIK
# ==========================================
st.markdown("---")
total_data = sum(d['count'] for d in db_stats.values())
st.caption(f"🤖 **System Status:** Database Connected | Total Analisa Terindex: **{total_data} item**")
