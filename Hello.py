import streamlit as st
import pandas as pd
import os
import json # Import json for parsing potential JSON strings if needed

# --- CONFIG APLIKASI ---
st.set_page_config(
    page_title="The Gems Grandmaster",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI BANTU ---
@st.cache_data
def load_ahsp_master(file_path):
    """Memuat data master AHSP dan mengembalikan DataFrame."""
    try:
        df = pd.read_excel(file_path)
        # Pastikan kolom bidang ada dan ubah ke lowercase untuk konsistensi
        if 'bidang' in df.columns:
            df['bidang'] = df['bidang'].str.lower()
        return df
    except FileNotFoundError:
        st.error(f"File master AHSP tidak ditemukan di: {file_path}")
        return pd.DataFrame() # Mengembalikan DataFrame kosong jika file tidak ditemukan
    except Exception as e:
        st.error(f"Error saat memuat master AHSP: {e}")
        return pd.DataFrame()

def cek_status_database(master_df):
    """Mengecek status ketersediaan data untuk setiap modul."""
    status = {
        "sda": False,
        "cipta_karya": False,
        "bina_marga": False
    }
    if not master_df.empty:
        if 'sda' in master_df['bidang'].unique():
            status["sda"] = True
        if 'cipta_karya' in master_df['bidang'].unique():
            status["cipta_karya"] = True
        if 'bina_marga' in master_df['bidang'].unique():
            status["bina_marga"] = True
    return status

def render_card(title, icon, status, count=None):
    """Merender kartu status untuk setiap modul."""
    if status:
        status_text = "Active"
        status_color = "green"
        count_text = f" ({count} items)" if count is not None else ""
        bg_color = "#E6FFE6" # Light green
    else:
        status_text = "Coming Soon"
        status_color = "red"
        count_text = ""
        bg_color = "#FFCCCC" # Light red

    st.markdown(
        f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: {bg_color};
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        ">
            <h3>{icon} {title}</h3>
            <p>Status: <b style='color:{status_color}'>{status_text}</b>{count_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- MAIN APLIKASI ---
st.title("💎 The Gems Grandmaster - Aplikasi RAB SNI 2025")
st.markdown("---")

st.info("Selamat datang di The Gems Grandmaster! Aplikasi ini dirancang untuk membantu Anda menyusun Rencana Anggaran Biaya (RAB) berdasarkan standar SNI, didukung oleh data terbaru dan modul kecerdasan buatan.")

# Pastikan folder data ada
if not os.path.exists('data'):
    os.makedirs('data')

# Path ke file master AHSP
ahsp_master_path = 'data/db_ahsp_master.xlsx'

# # Ciptakan file db_ahsp_master.xlsx dummy jika belum ada
# if not os.path.exists(ahsp_master_path):
#     dummy_df = pd.DataFrame(columns=['bidang', 'kode_ahsp', 'uraian_pekerjaan', 'satuan', 'tenaga', 'bahan', 'alat', 'overhead_default'])
#     dummy_df.to_excel(ahsp_master_path, index=False)
#     st.warning("File `db_ahsp_master.xlsx` tidak ditemukan. Dummy file telah dibuat.")
#     st.info("Anda perlu mengisi file `data/db_ahsp_master.xlsx` dengan data AHSP yang valid agar modul RAB aktif.")


df_master_ahsp = load_ahsp_master(ahsp_master_path)
status_modul = cek_status_database(df_master_ahsp)

st.header("Modul RAB Tersedia")
col1, col2, col3 = st.columns(3)

with col1:
    sda_count = df_master_ahsp[df_master_ahsp['bidang'] == 'sda'].shape[0] if not df_master_ahsp.empty else 0
    render_card("SDA (Sumber Daya Air)", "🌊", status_modul["sda"], sda_count)
with col2:
    cipta_karya_count = df_master_ahsp[df_master_ahsp['bidang'] == 'cipta_karya'].shape[0] if not df_master_ahsp.empty else 0
    render_card("Cipta Karya", "🏢", status_modul["cipta_karya"], cipta_karya_count)
with col3:
    bina_marga_count = df_master_ahsp[df_master_ahsp['bidang'] == 'bina_marga'].shape[0] if not df_master_ahsp.empty else 0
    render_card("Bina Marga", "🛣️", status_modul["bina_marga"], bina_marga_count)

st.header("Fitur Tambahan")
col_ai, col_other = st.columns(2)
with col_ai:
    render_card("AI Construction Consultant", "🤖", True) # AI consultant selalu aktif
with col_other:
    render_card("Manajemen Proyek", "📊", False) # Contoh modul coming soon

st.markdown("---")
st.subheader("Statistik Database AHSP")
if not df_master_ahsp.empty:
    st.write(f"Total item AHSP terindeks: {df_master_ahsp.shape[0]}")
    st.write(f"Bidang yang terdaftar: {', '.join(df_master_ahsp['bidang'].unique())}")
else:
    st.write("Database AHSP master kosong atau tidak ditemukan.")

st.markdown(
    """
    <style>
    .st-emotion-cache-1f0w4l1 { /* Adjust sidebar width */
        width: 250px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.title("Navigasi")
st.sidebar.markdown("""
- [🏠 Home](/)
- [🌊 SDA](1_%F0%9F%8C%8A_SDA)
- [🏢 Cipta Karya](2_%F0%9F%9A%A7_Cipta_Karya)
- [🛣️ Bina Marga](3_%F0%9F%9A%A7_Bina_Marga)
- [🤖 AI Consultant](4_%F0%9F%A4%96_AI_Consultant)
""")

# Opsional: Tampilkan beberapa baris pertama dari master AHSP
# if not df_master_ahsp.empty:
#     st.subheader("Preview Data Master AHSP")
#     st.dataframe(df_master_ahsp.head())
