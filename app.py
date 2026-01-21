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
# 1. LOAD DATABASE (VERSI PINTAR/ROBUST)
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    
    # Cek keberadaan file
    if not os.path.exists(path):
        st.warning(f"Database {path} belum ada. Mode Demo Aktif.")
        # Mock Data Lengkap untuk Demo
        return pd.DataFrame({
            "kode_ahsp": ["T.01.Contoh", "B.05.Beton"],
            "uraian_pekerjaan": ["Galian Tanah Manual", "Cor Beton K-175"],
            "satuan": ["m3", "m3"],
            "metode": ["Manual", "Mekanis"],
            "tenaga_detail": ["Pekerja (L.01) 0.750 OH; Mandor (L.04) 0.025 OH", "Pekerja 1.0 OH; Tukang 0.5 OH"],
            "bahan_detail": ["-", "Semen Portland 320 kg; Pasir Beton 0.76 m3; Kerikil 1.0 m3"],
            "alat_detail": ["-", "Concrete Mixer 0.25 Sewa-Hari"],
            "catatan": ["-", "-"]
        })
    
    # --- LOGIKA AUTO-FIX HEADER EXCEL ---
    try:
        # Percobaan 1: Baca normal (Header di baris 1)
        df = pd.read_excel(path, sheet_name=0)
        
        # Bersihkan nama kolom (hapus spasi, ubah ke huruf kecil)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Cek apakah kolom kunci 'kode_ahsp' ditemukan?
        if "kode_ahsp" not in df.columns:
            # Percobaan 2: Mungkin Header ada di Baris 2? (header=1)
            # Ini mengatasi masalah file Excel Anda yang baris 1-nya berisi kalimat chat
            df = pd.read_excel(path, sheet_name=0, header=1)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Cek Final
        if "kode_ahsp" not in df.columns:
            st.error("🚨 Gagal membaca Database! Sistem tidak menemukan kolom 'kode_ahsp'.")
            st.write("Kolom yang terbaca:", df.columns.tolist())
            st.warning("Tips: Pastikan judul kolom ada di Baris 1 atau Baris 2 Excel.")
            st.stop()

        return df

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca Excel: {e}")
        st.stop()

df = load_database()

# ==============================
# 2. FUNGSI PARSING PINTAR (REGEX)
# ==============================
def smart_parse_resource(text_string):
    """
    Mengubah teks "Semen 50 kg; Pasir 0.5 m3" menjadi Dictionary.
    """
    resources = {}
    # Handle NaN / Float / Empty
    if pd.isna(text_string) or str(text_string).strip() in ["-", "", "nan"]:
        return resources
    
    # Pecah berdasarkan titik koma (;)
    parts = str(text_string).split(';')
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        # Regex: Cari angka (integer/desimal) di akhir atau tengah string
        # Pola: Ambil nama (Group 1) dan Angka (Group 2)
        match = re.search(r'^(.*?)\s+([\d\.,]+)\s*([a-zA-Z]*)$', part) 
        # Note: Regex disederhanakan untuk menangkap angka desimal lebih fleksibel
        
        # Fallback regex jika yang diatas gagal (misal angka di tengah)
        if not match:
             match = re.search(r'^(.*?)\s+([\d\.]+)', part)

        if match:
            nama = match.group(1).strip()
            angka_str = match.group(2).replace(',', '.') # Ubah koma jadi titik jika ada
            try:
                angka = float(angka_str)
                resources[nama] = angka
            except ValueError:
                pass
            
    return resources

# ==============================
# 3. INTERFACE (SIDEBAR)
# ==============================
st.sidebar.header("🛠️ Input Analisa")

if df.empty:
    st.error("Database Kosong!")
    st.stop()

# Dropdown Pilih Item
kode_terpilih = st.sidebar.selectbox("Pilih Kode AHSP:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

# Tampilkan Info Item
st.info(f"**{row['uraian_pekerjaan']}**")
st.caption(f"Satuan: {row['satuan']} | Metode: {row['metode']}")

volume = st.number_input(f"Volume Pekerjaan ({row['satuan']})", value=1.0, step=0.1)

# --- AUTO-GENERATE INPUT FORM ---
koef_tenaga = smart_parse_resource(row.get('tenaga_detail', '-'))
koef_bahan = smart_parse_resource(row.get('bahan_detail', '-'))
koef_alat = smart_parse_resource(row.get('alat_detail', '-'))

input_harga_tenaga = {}
input_harga_bahan = {}
input_harga_alat = {}

# Form Input Dinamis
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
# 4. TOMBOL EKSEKUSI
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
    
    if "boq" not in st.session_state:
        st.session_state.boq = []
    st.session_state.boq.append(hasil)
    st.success("Item berhasil masuk keranjang BOQ!")

# ==============================
# 5. HASIL & REKAP (TABLE)
# ==============================
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
            "total": st.column_config.NumberColumn("Total Harga", format="Rp %.0f"),
        },
        use_container_width=True
    )
    
    col1, col2, col3, col4 = st.columns(4)
    # Hitung total kali volume (karena di dataframe data satuan, kita perlu total harga)
    grand_total = boq_df['total'].sum()
    
    col1.metric("Total Upah", f"Rp {boq_df['hsp_tenaga'].dot(boq_df['volume']):,.0f}")
    col2.metric("Total Bahan", f"Rp {boq_df['hsp_bahan'].dot(boq_df['volume']):,.0f}")
    col3.metric("Total Alat", f"Rp {boq_df['hsp_alat'].dot(boq_df['volume']):,.0f}")
    col4.metric("GRAND TOTAL", f"Rp {grand_total:,.0f}")

    if st.button("Hapus Semua Data"):
        st.session_state.boq = []
        st.rerun()
else:
    st.info("Belum ada item pekerjaan yang dihitung.")

# Debugger (Opsional)
# with st.expander("Lihat Data Mentah"):
#     st.write(row.to_dict())
