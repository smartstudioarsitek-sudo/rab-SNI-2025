import streamlit as st
import pandas as pd
import os
import re

# ==============================
# 1. CONFIG & HEADER (Wajib Paling Atas)
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
# 2. LOAD DATABASE (VERSI AUTO-SEARCH SHEET)
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    
    if not os.path.exists(path):
        st.error(f"File database tidak ditemukan di: {path}")
        st.stop()
    
    try:
        # Buka File Excel tanpa memuat isinya dulu untuk cek daftar sheet
        xls = pd.ExcelFile(path)
        sheet_names = xls.sheet_names
        
        # Loop untuk mencari sheet mana yang punya kolom 'kode_ahsp'
        for sheet in sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            
            # Bersihkan nama kolom (hapus spasi, huruf kecil)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            
            # Cek apakah ini sheet yang benar?
            if "kode_ahsp" in df.columns:
                return df # Ketemu! Kembalikan data ini.
        
        # Jika loop selesai tapi tidak ketemu
        st.error("🚨 Gagal menemukan data! Tidak ada sheet yang memiliki kolom 'kode_ahsp'.")
        st.write("Sheet yang diperiksa:", sheet_names)
        st.stop()

    except Exception as e:
        st.error(f"Error membaca Excel: {e}")
        st.stop()

df = load_database()

# ==============================
# 3. FUNGSI PARSING (KOEFISIEN)
# ==============================
def smart_parse_resource(text_string):
    resources = {}
    if pd.isna(text_string) or str(text_string).strip() in ["-", "", "nan"]:
        return resources
    
    # Pecah string berdasarkan titik koma
    parts = str(text_string).split(';')
    for part in parts:
        part = part.strip()
        if not part: continue
        
        # Regex untuk menangkap Nama & Angka (Flexible)
        match = re.search(r'^(.*?)\s+([\d\.,]+)\s*([a-zA-Z]*)$', part)
        if not match: match = re.search(r'^(.*?)\s+([\d\.]+)', part)
        
        if match:
            nama = match.group(1).strip()
            try:
                # Ubah koma jadi titik biar bisa dihitung desimal
                angka = float(match.group(2).replace(',', '.'))
                resources[nama] = angka
            except: pass
    return resources

# ==============================
# 4. INTERFACE (SIDEBAR)
# ==============================
st.sidebar.header("🛠️ Input Analisa")

if df.empty:
    st.error("Database Kosong!")
    st.stop()

# Dropdown Pilihan
kode_terpilih = st.sidebar.selectbox("Pilih Kode AHSP:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

# Tampilkan Info Item
st.info(f"**{row['uraian_pekerjaan']}**")
st.caption(f"Satuan: {row['satuan']} | Metode: {row['metode']}")
volume = st.number_input(f"Volume Pekerjaan ({row['satuan']})", value=1.0, step=0.1)

# Parsing Koefisien Otomatis
koef_tenaga = smart_parse_resource(row.get('tenaga_detail', '-'))
koef_bahan = smart_parse_resource(row.get('bahan_detail', '-'))
koef_alat = smart_parse_resource(row.get('alat_detail', '-'))

input_harga_tenaga = {}
input_harga_bahan = {}
input_harga_alat = {}

# --- Form Input Harga (Dinamis) ---
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
# 5. EKSEKUSI & HASIL
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
    st.success("✅ Item berhasil masuk keranjang BOQ!")

# Tampilkan Tabel BOQ
st.divider()
st.subheader("📋 Bill of Quantities (BOQ)")

if "boq" in st.session_state and st.session_state.boq:
    boq_df = pd.DataFrame(st.session_state.boq)
    
    # Tampilkan Tabel Rinci
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
    
    # Tampilkan Grand Total
    grand_total = boq_df['total'].sum()
    st.metric("GRAND TOTAL RAB", f"Rp {grand_total:,.0f}")
    
    if st.button("Hapus Semua Data"):
        st.session_state.boq = []
        st.rerun()
else:
    st.info("Belum ada item pekerjaan yang dihitung. Silakan pilih item di menu kiri.")
