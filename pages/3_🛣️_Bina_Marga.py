import streamlit as st
import pandas as pd

try:
    from engine import sda_engine
except ImportError:
    st.error("🚨 Engine tidak ditemukan!")
    st.stop()

st.set_page_config(page_title="Modul Bina Marga", page_icon="🛣️", layout="wide")
st.title("🛣️ Modul Bina Marga (Jalan & Jembatan)")
st.caption("Spesialisasi: Aspal, Perkerasan, & Alat Berat (Mode Lite)")

if "boq_bm" not in st.session_state:
    st.session_state.boq_bm = []

# ==========================================
# 1. DATABASE MANDIRI (DEFAULT DATA BM)
# ==========================================
def get_default_bm():
    data = [
        {
            "kode": "Div.3.2", 
            "uraian": "Galian Biasa untuk Drainase & Saluran Air", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 0.10, "Mandor": 0.01},
            "bahan": {},
            "alat": {"Excavator": 0.035, "Dump Truck": 0.050}
        },
        {
            "kode": "Div.5.1", 
            "uraian": "Lapis Pondasi Agregat Kelas A (LPA)", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 0.20, "Mandor": 0.02},
            "bahan": {"Agregat Kelas A": 1.20}, # Faktor gembur
            "alat": {"Wheel Loader": 0.015, "Motor Grader": 0.010, "Vibratory Roller": 0.012, "Water Tanker": 0.010}
        },
        {
            "kode": "Div.6.3", 
            "uraian": "Laston Lapis Aus (AC-WC)", 
            "satuan": "Ton",
            "tenaga": {"Pekerja": 0.30, "Mandor": 0.03},
            "bahan": {"Aspal Cair": 0.06, "Agregat Kasar": 0.45, "Agregat Halus": 0.45, "Filler": 0.04},
            "alat": {"Asphalt Mixing Plant": 0.010, "Asphalt Finisher": 0.015, "Tandem Roller": 0.020, "Pneumatic Tire Roller": 0.020}
        }
    ]
    return pd.DataFrame(data)

# --- SIDEBAR ---
sumber = st.sidebar.radio("Pilih Database:", ["Data Contoh (Jalan)", "Upload Excel Proyek"], key="src_bm")
if sumber == "Data Contoh (Jalan)":
    df_ahsp = get_default_bm()
else:
    # Logic upload sama seperti CK/SDA
    f = st.sidebar.file_uploader("Upload Excel", type=["xlsx"])
    df_ahsp = pd.read_excel(f) if f else pd.DataFrame()

# ==========================================
# 2. HARGA SATUAN (Alat Berat Dominan)
# ==========================================
st.sidebar.divider()
st.sidebar.header("💰 Harga Sewa Alat & Material")

default_harga = {
    "Pekerja": 110000, "Mandor": 160000,
    "Agregat Kelas A": 250000, "Aspal Cair": 12000, # per kg
    "Excavator": 450000, "Dump Truck": 300000, "Motor Grader": 600000,
    "Vibratory Roller": 500000, "Asphalt Finisher": 800000
}

with st.sidebar.expander("🚜 Update Sewa Alat (Per Jam)"):
    h_excavator = st.number_input("Sewa Excavator", value=default_harga["Excavator"])
    h_truck = st.number_input("Sewa Dump Truck", value=default_harga["Dump Truck"])
    default_harga["Excavator"] = h_excavator
    default_harga["Dump Truck"] = h_truck

# ==========================================
# 3. CORE APPS
# ==========================================
if not df_ahsp.empty:
    pilihan = st.selectbox("Pilih Pekerjaan Jalan:", df_ahsp['uraian'].unique())
    row = df_ahsp[df_ahsp['uraian'] == pilihan].iloc[0]
    
    vol = st.number_input("Volume", value=100.0, step=10.0)
    st.caption(f"Satuan: {row['satuan']}")
    
    if st.button("➕ Tambah ke RAB Jalan"):
        # Matcher harga sederhana
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
        st.session_state.boq_bm.append(hasil)
        st.success("Masuk!")

# ==========================================
# 4. TABEL OUTPUT
# ==========================================
st.divider()
if st.session_state.boq_bm:
    df_view = pd.DataFrame([{
        "Uraian": i['meta']['uraian'], "Vol": i['meta']['volume'], 
        "HSP": i['biaya']['hsp'], "Total": i['biaya']['total_final']
    } for i in st.session_state.boq_bm])
    
    st.dataframe(df_view, use_container_width=True)
    st.markdown(f"### Total Jalan: Rp {df_view['Total'].sum():,.0f}")
    
    # Download
    xlsx = sda_engine.export_to_excel(df_view)
    st.download_button("📥 Download Excel", xlsx, "RAB_Jalan.xlsx")
else:
    st.warning("Silakan input item pekerjaan jalan.")
