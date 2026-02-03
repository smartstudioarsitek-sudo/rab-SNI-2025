import streamlit as st
import pandas as pd

# Import Engine (Pastikan file sda_engine.py ada di folder engine)
try:
    from engine import sda_engine
except ImportError:
    st.error("🚨 File engine/sda_engine.py tidak ditemukan!")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Modul Cipta Karya", page_icon="🏗️", layout="wide")
st.title("🏗️ Modul Cipta Karya (Gedung)")
st.caption("Spesialisasi: Struktur, Arsitektur, & MEP (Mode Lite)")

# Init Session State
if "boq_ck" not in st.session_state:
    st.session_state.boq_ck = []

# ==========================================
# 1. DATABASE MANDIRI (DEFAULT DATA)
# ==========================================
def get_default_ck():
    """Data Dummy agar aplikasi langsung jalan tanpa upload file"""
    data = [
        {
            "kode": "A.4.4.1", 
            "uraian": "Pasangan Dinding Bata Merah 1:4", 
            "satuan": "m2",
            "tenaga": {"Pekerja": 0.300, "Tukang Batu": 0.100, "Mandor": 0.015},
            "bahan": {"Bata Merah": 70.00, "Semen PC": 11.50, "Pasir Pasang": 0.043},
            "alat": {}
        },
        {
            "kode": "A.4.1.1", 
            "uraian": "Beton Mutu fc = 19.3 MPa (K-225)", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 1.650, "Tukang Batu": 0.275, "Mandor": 0.083},
            "bahan": {"Semen PC": 371.00, "Pasir Beton": 0.698, "Kerikil": 1.047},
            "alat": {"Concrete Mixer": 0.250} # Sewa molen
        },
        {
            "kode": "P.01", 
            "uraian": "Pemasangan Lantai Keramik 40x40", 
            "satuan": "m2",
            "tenaga": {"Pekerja": 0.700, "Tukang Keramik": 0.350, "Mandor": 0.035},
            "bahan": {"Keramik 40x40": 1.05, "Semen PC": 10.00, "Pasir": 0.045, "Semen Warna": 1.50},
            "alat": {}
        }
    ]
    return pd.DataFrame(data)

# --- SIDEBAR ---
st.sidebar.header("📂 Sumber Data")
sumber = st.sidebar.radio("Pilih Database:", ["Data Contoh (Gedung)", "Upload Excel Proyek"], key="src_ck")

if sumber == "Data Contoh (Gedung)":
    df_ahsp = get_default_ck()
    st.sidebar.success("✅ 3 Item Contoh Terload")
else:
    f = st.sidebar.file_uploader("Upload Excel Analisa", type=["xlsx"])
    if f:
        try:
            df_ahsp = pd.read_excel(f)
            st.sidebar.success(f"✅ {len(df_ahsp)} Item Terload")
        except: st.sidebar.error("Gagal baca file")
    else:
        df_ahsp = pd.DataFrame()

# ==========================================
# 2. HARGA SATUAN (SHS)
# ==========================================
st.sidebar.divider()
st.sidebar.header("💰 Harga Dasar Material")

# Harga Default Gedung
default_harga = {
    "Pekerja": 120000, "Tukang Batu": 140000, "Mandor": 170000,
    "Semen PC": 1450, "Pasir Pasang": 280000, "Bata Merah": 900,
    "Kerikil": 300000, "Keramik 40x40": 65000, "Concrete Mixer": 150000
}

# Input Manual Cepat
with st.sidebar.expander("📝 Update Harga Cepat"):
    h_semen = st.number_input("Harga Semen (per Kg)", value=default_harga["Semen PC"])
    h_bata = st.number_input("Harga Bata Merah (per Bh)", value=default_harga["Bata Merah"])
    default_harga["Semen PC"] = h_semen
    default_harga["Bata Merah"] = h_bata

# ==========================================
# 3. CORE APPS
# ==========================================
if not df_ahsp.empty:
    st.info("💡 Silakan pilih item pekerjaan gedung di bawah ini:")
    
    # Pilih Item
    pilihan = st.selectbox("Pilih Pekerjaan:", df_ahsp['uraian'].unique())
    row = df_ahsp[df_ahsp['uraian'] == pilihan].iloc[0]
    
    c1, c2 = st.columns(2)
    vol = c1.number_input("Volume Pekerjaan", value=10.0, step=1.0)
    c2.text_input("Satuan", value=row['satuan'], disabled=True)
    
    # Hitung
    if st.button("➕ Tambah ke RAB Gedung"):
        # Match harga otomatis
        def match(x): 
            for k,v in default_harga.items():
                if k.lower() in str(x).lower(): return v
            return 0
            
        hasil = sda_engine.hitung_rab_lengkap(
            kode_ahsp=row['kode'], uraian=row['uraian'], volume=vol, satuan=row['satuan'],
            koef_tenaga=row['tenaga'], harga_tenaga={k:match(k) for k in row['tenaga']},
            koef_bahan=row['bahan'], harga_bahan={k:match(k) for k in row['bahan']},
            koef_alat=row['alat'], harga_alat={k:match(k) for k in row['alat']}
        )
        st.session_state.boq_ck.append(hasil)
        st.success("Masuk!")

# ==========================================
# 4. TABEL OUTPUT
# ==========================================
st.divider()
if st.session_state.boq_ck:
    df_view = pd.DataFrame([{
        "Uraian": i['meta']['uraian'], "Vol": i['meta']['volume'], 
        "HSP": i['biaya']['hsp'], "Total": i['biaya']['total_final']
    } for i in st.session_state.boq_ck])
    
    st.dataframe(df_view, use_container_width=True)
    st.markdown(f"### Total Gedung: Rp {df_view['Total'].sum():,.0f}")
    
    # Download
    xlsx = sda_engine.export_to_excel(df_view)
    st.download_button("📥 Download Excel", xlsx, "RAB_Gedung.xlsx")
else:
    st.warning("Keranjang RAB masih kosong.")
