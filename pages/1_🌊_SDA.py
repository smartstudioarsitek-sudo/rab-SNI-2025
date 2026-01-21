import streamlit as st
import pandas as pd
import os
import re

# ==============================
# CONFIG HALAMAN
# ==============================
st.set_page_config(page_title="Modul SDA", layout="wide")

# Import Engine
import sys
sys.path.append('.')
try:
    from engine import sda_engine
except ModuleNotFoundError:
    st.error("🚨 Modul 'engine' tidak ditemukan.")
    st.stop()

st.title("🌊 Modul Sumber Daya Air (SDA)")
st.caption("Perhitungan AHSP Bidang SDA - Basis Data Terpusat")

# ==============================
# 1. LOAD DATABASE AHSP
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    if not os.path.exists(path):
        st.error(f"Database tidak ditemukan di: {path}")
        st.stop()
    try:
        xls = pd.ExcelFile(path)
        for sheet in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            if "kode_ahsp" in df.columns:
                return df
        st.error("Tidak ada sheet yang valid (harus ada kolom 'kode_ahsp')")
        st.stop()
    except Exception as e:
        st.error(f"Error DB: {e}")
        st.stop()

df = load_database()

# ==============================
# 2. LOAD HARGA SATUAN (SHS) - VERSI FORMAT PDF 🌟
# ==============================
def clean_currency(value):
    """Mengubah 'Rp 10,000.00' menjadi 10000.0"""
    try:
        if pd.isna(value): return 0.0
        # Ubah jadi string, buang 'Rp', buang titik (ribuan), ganti koma jadi titik (desimal)
        # Atau sesuaikan format Indonesia: Titik = Ribuan, Koma = Desimal
        str_val = str(value).lower().replace("rp", "").strip()
        
        # Cek format: jika ada koma di akhir (misal 10.000,00)
        if "," in str_val and "." in str_val:
            str_val = str_val.replace(".", "") # Buang pemisah ribuan
            str_val = str_val.replace(",", ".") # Ubah pemisah desimal
        elif "," in str_val: # Misal 10,000 (format luar negeri) atau 10,5
             str_val = str_val.replace(",", "") 
        
        return float(str_val)
    except:
        return 0.0

def load_shs_data(uploaded_file):
    try:
        df_shs = pd.read_excel(uploaded_file)
        # Standarisasi Header: huruf kecil semua
        df_shs.columns = [str(c).strip().lower() for c in df_shs.columns]
        
        # 1. Cari Kolom NAMA (Bisa 'uraian', 'nama bahan', 'nama bahan dan upah')
        col_uraian = next((c for c in df_shs.columns if "nama" in c or "uraian" in c), None)
        
        # 2. Cari Kolom HARGA (Bisa 'harga', 'harga satuan', 'harga bahan/upah')
        col_harga = next((c for c in df_shs.columns if "harga" in c), None)
        
        if col_uraian and col_harga:
            # Bersihkan harga (hapus Rp)
            df_shs['harga_clean'] = df_shs[col_harga].apply(clean_currency)
            
            # Buat Dictionary Pencarian
            price_dict = dict(zip(
                df_shs[col_uraian].astype(str).str.lower().str.strip(), 
                df_shs['harga_clean']
            ))
            return price_dict, len(price_dict)
        else:
            return {}, 0
    except Exception:
        return {}, 0

# ==============================
# 3. SIDEBAR: UPLOAD & INPUT
# ==============================
st.sidebar.header("📥 Data Harga Satuan (SHS)")
uploaded_shs = st.sidebar.file_uploader("Upload File Excel SHS (Format PDF OK)", type=["xlsx"])

shs_prices = {}
if uploaded_shs:
    shs_prices, count = load_shs_data(uploaded_shs)
    if count > 0:
        st.sidebar.success(f"✅ {count} harga berhasil dimuat!")
    else:
        st.sidebar.warning("⚠️ Kolom 'Nama Bahan' atau 'Harga' tidak ditemukan.")

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Analisa Pekerjaan")

# Pilih Item
kode_terpilih = st.sidebar.selectbox("Pilih Item Pekerjaan:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

st.info(f"**{row['uraian_pekerjaan']}**")
st.caption(f"Satuan: {row['satuan']} | Metode: {row['metode']}")
volume = st.number_input(f"Volume ({row['satuan']})", value=1.0, step=0.1)

# Helper Parsing
def smart_parse_resource(text_string):
    resources = {}
    if pd.isna(text_string) or str(text_string).strip() in ["-", "", "nan"]:
        return resources
    parts = str(text_string).split(';')
    for part in parts:
        # Regex yang lebih toleran
        match = re.search(r'^(.*?)\s+([\d\.,]+)\s*([a-zA-Z]*)$', part.strip())
        if not match: match = re.search(r'^(.*?)\s+([\d\.]+)', part.strip())
        if match:
            try:
                nama = match.group(1).strip()
                angka = float(match.group(2).replace(',', '.'))
                resources[nama] = angka
            except: pass
    return resources

koef_tenaga = smart_parse_resource(row.get('tenaga_detail', '-'))
koef_bahan = smart_parse_resource(row.get('bahan_detail', '-'))
koef_alat = smart_parse_resource(row.get('alat_detail', '-'))

input_harga_tenaga = {}
input_harga_bahan = {}
input_harga_alat = {}

# --- FUNGSI AUTO-FILL PINTAR (IGNORING KURUNG) ---
def get_auto_price(resource_name, default_val=0.0):
    # Nama di DB: "Semen (PC)" -> kita ambil "semen" saja untuk kunci pencarian
    res_clean = resource_name.lower().split('(')[0].strip()
    
    # 1. Coba Exact Match di Dictionary SHS
    for name_shs, price in shs_prices.items():
        # Nama di SHS: "Semen Portland" -> kita ambil "semen"
        shs_clean = name_shs.split('(')[0].strip()
        
        # Logika Cocok-cocokan:
        # Apakah "semen" ada di "semen portland"? YA.
        # Apakah "pasir" ada di "pasir beton"? YA.
        if res_clean in shs_clean or shs_clean in res_clean:
            return float(price)
            
    return default_val

# Form Input
if koef_tenaga:
    st.sidebar.subheader("👷 Upah Tenaga")
    for nama, koef in koef_tenaga.items():
        default_price = get_auto_price(nama, 120000.0)
        input_harga_tenaga[nama] = st.sidebar.number_input(f"Upah {nama}", value=default_price, step=5000.0)

if koef_bahan:
    st.sidebar.subheader("🧱 Harga Bahan")
    for nama, koef in koef_bahan.items():
        default_price = get_auto_price(nama, 0.0)
        input_harga_bahan[nama] = st.sidebar.number_input(f"Harga {nama}", value=default_price, step=1000.0)

if koef_alat:
    st.sidebar.subheader("🚜 Sewa Alat")
    for nama, koef in koef_alat.items():
        default_price = get_auto_price(nama, 0.0)
        input_harga_alat[nama] = st.sidebar.number_input(f"Sewa {nama}", value=default_price, step=10000.0)

# ==============================
# 4. EKSEKUSI
# ==============================
if st.button("🚀 Hitung RAB Item Ini", type="primary"):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=kode_terpilih,
        uraian_pekerjaan=row['uraian_pekerjaan'],
        satuan=row['satuan'],
        volume=volume,
        harga_tenaga=input_harga_tenaga, koefisien_tenaga=koef_tenaga,
        harga_bahan=input_harga_bahan, koefisien_bahan=koef_bahan,
        harga_alat=input_harga_alat, koefisien_alat=koef_alat
    )
    if "boq" not in st.session_state: st.session_state.boq = []
    st.session_state.boq.append(hasil)
    st.success("Masuk BOQ!")

st.divider()
st.subheader("📋 Bill of Quantities (BOQ)")

if "boq" in st.session_state and st.session_state.boq:
    boq_df = pd.DataFrame(st.session_state.boq)
    st.dataframe(boq_df, use_container_width=True)
    st.metric("GRAND TOTAL", f"Rp {boq_df['total'].sum():,.0f}")
    if st.button("Reset"):
        st.session_state.boq = []
        st.rerun()
else:
    st.info("Belum ada data.")
