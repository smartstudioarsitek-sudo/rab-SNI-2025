import streamlit as st
import pandas as pd
import os
import re

# ==============================
# CONFIG & HEADER
# ==============================
st.set_page_config(page_title="JIAT Smart Studio", layout="wide")
st.title("JIAT Smart Studio – Super App Konstruksi")
st.caption("Engine: SDA + Cipta Karya + Bina Marga | Validasi AHSP 2025")

# Import Engine
try:
    from engine import sda_engine
except ModuleNotFoundError:
    st.error("🚨 Modul 'engine' tidak ditemukan. Pastikan folder engine dan file sda_engine.py ada.")
    st.stop()

# ==============================
# 1. LOAD DATABASE (VERSI NORMAL - FILE SUDAH RAPI)
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    
    if not os.path.exists(path):
        st.error("File database tidak ditemukan.")
        st.stop()
    
    # BACA EXCEL SECARA NORMAL (Header di Baris 1)
    # sheet_name=0 artinya ambil sheet paling pertama
    df = pd.read_excel(path, sheet_name=0)
    
    # Bersihkan nama kolom (jaga-jaga kalau ada spasi)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
    # Validasi
    if "kode_ahsp" not in df.columns:
        st.error("🚨 Kolom 'kode_ahsp' tidak ditemukan.")
        st.write("Kolom yang terbaca:", df.columns.tolist())
        st.stop()
        
    return df

df = load_database()

# ==============================
# 2. FUNGSI PARSING (KOEFISIEN)
# ==============================
def smart_parse_resource(text_string):
    resources = {}
    if pd.isna(text_string) or str(text_string).strip() in ["-", "", "nan"]:
        return resources
    
    parts = str(text_string).split(';')
    for part in parts:
        part = part.strip()
        if not part: continue
        # Regex cari Nama & Angka
        match = re.search(r'^(.*?)\s+([\d\.,]+)\s*([a-zA-Z]*)$', part)
        if not match: match = re.search(r'^(.*?)\s+([\d\.]+)', part)
        
        if match:
            nama = match.group(1).strip()
            try:
                # Ganti koma jadi titik biar bisa dihitung
                angka = float(match.group(2).replace(',', '.'))
                resources[nama] = angka
            except: pass
    return resources

# ==============================
# 3. INTERFACE (SIDEBAR)
# ==============================
st.sidebar.header("🛠️ Input Analisa")

if df.empty:
    st.error("Database Kosong!")
    st.stop()

# Dropdown
kode_terpilih = st.sidebar.selectbox("Pilih Kode AHSP:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

# Info Item
st.info(f"**{row['uraian_pekerjaan']}**")
st.caption(f"Satuan: {row['satuan']} | Metode: {row['metode']}")
volume = st.number_input(f"Volume ({row['satuan']})", value=1.0, step=0.1)

# Parsing Koefisien
koef_tenaga = smart_parse_resource(row.get('tenaga_detail', '-'))
koef_bahan = smart_parse_resource(row.get('bahan_detail', '-'))
koef_alat = smart_parse_resource(row.get('alat_detail', '-'))

input_harga_tenaga = {}
input_harga_bahan = {}
input_harga_alat = {}

# Form Input Harga
if koef_tenaga:
    st.sidebar.subheader("👷 Upah Tenaga")
    for nama, koef in koef_tenaga.items():
        val = 150000.0 if "Mandor" in nama or "Tukang" in nama else 120000.0
        input_harga_tenaga[nama] = st.sidebar.number_input(f"Upah {nama}", value=val, step=5000.0)

if koef_bahan:
    st.sidebar.subheader("🧱 Harga Bahan")
    for nama, koef in koef_bahan.items():
        input_harga_bahan[nama] = st.sidebar.number_input(f"Harga {nama}", value=0.0, step=1000.0)

if koef_alat:
    st.sidebar.subheader("🚜 Sewa Alat")
    for nama, koef in koef_alat.items():
        input_harga_alat[nama] = st.sidebar.number_input(f"Sewa {nama}", value=0.0, step=10000.0)

# ==============================
# 4. EKSEKUSI & HASIL
# ==============================
if st.button("🚀 Hitung RAB", type="primary"):
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
    
    st.dataframe(
        boq_df[["kode_ahsp", "uraian", "volume", "satuan", "hsp_tenaga", "hsp_bahan", "hsp_alat", "harga_satuan", "total"]],
        column_config={
            "hsp_tenaga": st.column_config.NumberColumn("Upah", format="Rp %.0f"),
            "hsp_bahan": st.column_config.NumberColumn("Bahan", format="Rp %.0f"),
            "hsp_alat": st.column_config.NumberColumn("Alat", format="Rp %.0f"),
            "harga_satuan": st.column_config.NumberColumn("HSP", format="Rp %.0f"),
            "total": st.column_config.NumberColumn("Total", format="Rp %.0f"),
        },
        use_container_width=True
    )
    
    grand_total = boq_df['total'].sum()
    st.metric("GRAND TOTAL RAB", f"Rp {grand_total:,.0f}")
    
    if st.button("Hapus Semua"):
        st.session_state.boq = []
        st.rerun()
else:
    st.info("Belum ada data.")
