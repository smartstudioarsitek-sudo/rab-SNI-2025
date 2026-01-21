import streamlit as st
import pandas as pd
import os
import re

# ==============================
# CONFIG HALAMAN
# ==============================
st.set_page_config(page_title="Modul SDA", layout="wide")

# Import Engine (Pastikan folder engine ada di root directory)
import sys
sys.path.append('.') # Trik agar folder engine terbaca dari subfolder pages
try:
    from engine import sda_engine
except ModuleNotFoundError:
    st.error("🚨 Modul 'engine' tidak ditemukan. Pastikan struktur folder benar.")
    st.stop()

st.title("🌊 Modul Sumber Daya Air (SDA)")
st.caption("Perhitungan AHSP Bidang SDA - Basis Data Terpusat")

# ==============================
# 1. LOAD DATABASE AHSP (Server)
# ==============================
@st.cache_data
def load_database():
    # Perhatikan path: naik satu folder (..) lalu masuk data
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
# 2. LOAD HARGA SATUAN (SHS) - FITUR BARU 🌟
# ==============================
# Fungsi untuk membaca file Excel SHS yang diupload user
def load_shs_data(uploaded_file):
    try:
        df_shs = pd.read_excel(uploaded_file)
        # Standarisasi nama kolom biar tidak error
        df_shs.columns = [str(c).strip().lower() for c in df_shs.columns]
        
        # Cari kolom yang mirip "uraian" dan "harga"
        col_uraian = next((c for c in df_shs.columns if "uraian" in c or "nama" in c), None)
        col_harga = next((c for c in df_shs.columns if "harga" in c), None)
        
        if col_uraian and col_harga:
            # Buat Dictionary: {"Semen": 1500, "Pasir": 200000}
            # Kita bersihkan nama resource (huruf kecil) agar pencarian lebih akurat
            price_dict = dict(zip(
                df_shs[col_uraian].astype(str).str.lower().str.strip(), 
                df_shs[col_harga]
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
uploaded_shs = st.sidebar.file_uploader("Upload File Excel SHS", type=["xlsx"])

shs_prices = {}
if uploaded_shs:
    shs_prices, count = load_shs_data(uploaded_shs)
    if count > 0:
        st.sidebar.success(f"✅ {count} harga berhasil dimuat!")
    else:
        st.sidebar.warning("⚠️ Gagal membaca harga. Pastikan ada kolom 'Uraian' dan 'Harga'.")

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Analisa Pekerjaan")

# Pilih Kode
kode_terpilih = st.sidebar.selectbox("Pilih Item Pekerjaan:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

# Info Item
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
        match = re.search(r'^(.*?)\s+([\d\.,]+)\s*([a-zA-Z]*)$', part.strip())
        if not match: match = re.search(r'^(.*?)\s+([\d\.]+)', part.strip())
        if match:
            try:
                nama = match.group(1).strip()
                angka = float(match.group(2).replace(',', '.'))
                resources[nama] = angka
            except: pass
    return resources

# Parsing Data
koef_tenaga = smart_parse_resource(row.get('tenaga_detail', '-'))
koef_bahan = smart_parse_resource(row.get('bahan_detail', '-'))
koef_alat = smart_parse_resource(row.get('alat_detail', '-'))

input_harga_tenaga = {}
input_harga_bahan = {}
input_harga_alat = {}

# --- FUNGSI AUTO-FILL HARGA ---
def get_auto_price(resource_name, default_val=0.0):
    # Coba cari di SHS (pakai huruf kecil semua biar cocok)
    name_key = resource_name.lower().strip()
    
    # Cari yang mengandung kata kuncinya (Partial Match)
    # Misal di DB "Semen (PC)", di SHS "Semen". Kita coba cocokkan.
    if name_key in shs_prices:
        return float(shs_prices[name_key])
    
    # Kalau exact match gak ketemu, cari manual di dict
    for k, v in shs_prices.items():
        if k in name_key or name_key in k: # Saling mencocokkan sebagian kata
            return float(v)
            
    return default_val

# Form Input (Otomatis Terisi jika SHS diupload)
if koef_tenaga:
    st.sidebar.subheader("👷 Upah Tenaga")
    for nama, koef in koef_tenaga.items():
        default_price = get_auto_price(nama, 120000.0) # Default kalau gak ketemu
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
