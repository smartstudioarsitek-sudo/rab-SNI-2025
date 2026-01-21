import streamlit as st
import pandas as pd
import sys
import os

# ==============================
# CONFIG & HEADER
# ==============================
st.set_page_config(page_title="Modul SDA", layout="wide")

# Import Engine
sys.path.append('.')
try:
    from engine import sda_engine
except:
    st.error("🚨 Engine tidak ditemukan. Pastikan folder 'engine' ada.")
    st.stop()

st.title("🌊 Modul Sumber Daya Air (SDA)")
st.caption("Database AHSP Terintegrasi (CSV System)")

# ==============================
# 1. LOAD DATABASE (OTOMATIS DARI GITHUB)
# ==============================
@st.cache_data
def load_database():
    # Arahkan ke file CSV yang baru diupload ke folder data
    path = "data/ahsp_sda_master.csv"
    
    if not os.path.exists(path):
        st.error(f"⚠️ Database tidak ditemukan di: {path}")
        st.info("Pastikan file 'ahsp_sda_master.csv' sudah diupload ke folder 'data' di GitHub.")
        st.stop()
        
    try:
        # Coba baca dengan pemisah KOMA (Standar Internasional)
        df = pd.read_csv(path, sep=",")
        
        # Jaga-jaga kalau CSV-nya pakai TITIK KOMA (Format Excel Indo)
        if len(df.columns) < 2:
            df = pd.read_csv(path, sep=";")
            
        # Bersihkan nama kolom
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error membaca CSV: {e}")
        st.stop()

# Panggil Fungsi Load
df_ahsp = load_database()

# ==============================
# 2. UPLOAD HARGA (USER INPUT)
# ==============================
st.sidebar.header("💰 Data Harga Satuan")
st.sidebar.caption("Upload file CSV harga proyek (Opsional)")

file_harga = st.sidebar.file_uploader("Upload harga.csv", type=["csv"])
dict_harga = {}

if file_harga:
    try:
        # Baca CSV Harga (Smart Detect Separator)
        df_h = pd.read_csv(file_harga)
        if len(df_h.columns) < 2:
            file_harga.seek(0)
            df_h = pd.read_csv(file_harga, sep=";")
            
        df_h.columns = [c.strip().lower() for c in df_h.columns]
        
        if 'nama' in df_h.columns and 'harga' in df_h.columns:
            dict_harga = dict(zip(
                df_h['nama'].astype(str).str.lower().str.strip(),
                df_h['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Harga Masuk")
        else:
            st.sidebar.error("CSV Harga harus punya kolom: nama, harga")
    except Exception as e:
        st.sidebar.error(f"Gagal baca harga: {e}")

# ==============================
# 3. INTERFACE ANALISA
# ==============================
st.divider()

if df_ahsp.empty:
    st.warning("Database kosong atau gagal dimuat.")
    st.stop()

# Dropdown Pilihan Pekerjaan
pilihan_label = df_ahsp['kode'].astype(str) + " | " + df_ahsp['uraian']
pilihan = st.selectbox("Pilih Item Pekerjaan:", options=pilihan_label)

# Ambil Data Baris Terpilih
kode_terpilih = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode_terpilih].iloc[0]

# Tampilkan Info
st.subheader(f"Analisa: {row['uraian']}")
col_vol, _ = st.columns([1, 3])
vol = col_vol.number_input(f"Volume ({row['satuan']})", value=1.0)

# ==============================
# 4. PARSING & AUTO-PRICE
# ==============================
def process_resources(text_koef, tipe):
    input_vals = {}
    koef_vals = {}
    
    if pd.isna(text_koef) or str(text_koef).strip() in ["-", "nan"]:
        return {}, {}

    items = str(text_koef).split(';')
    for item in items:
        # Regex ambil Nama & Angka
        import re
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        
        if match:
            nama = match.group(1).strip()
            koef = float(match.group(2))
            koef_vals[nama] = koef
            
            # Cari Harga Otomatis
            kunci = nama.lower()
            harga = 0.0
            
            # Cek di Dictionary Harga
            if kunci in dict_harga:
                harga = float(dict_harga[kunci])
            else:
                # Cek Parsial (Mirip)
                for k, v in dict_harga.items():
                    if k in kunci or kunci in k:
                        harga = float(v)
                        break
            
            # Default Harga Jika Tidak Ketemu (Biar tidak 0 banget)
            if harga == 0:
                if tipe == "upah": harga = 100000.0
                elif tipe == "bahan": harga = 0.0
                elif tipe == "alat": harga = 0.0

            input_vals[nama] = st.number_input(
                f"{nama}", value=harga, step=1000.0, key=f"{kode_terpilih}_{nama}"
            )
    return input_vals, koef_vals

# Layout 3 Kolom
c1, c2, c3 = st.columns(3)

with c1:
    st.info("👷 TENAGA")
    h_tenaga, k_tenaga = process_resources(row.get('tenaga', '-'), "upah")

with c2:
    st.warning("🧱 BAHAN")
    h_bahan, k_bahan = process_resources(row.get('bahan', '-'), "bahan")

with c3:
    st.success("🚜 ALAT")
    h_alat, k_alat = process_resources(row.get('alat', '-'), "alat")

# ==============================
# 5. HITUNG & HASIL
# ==============================
st.markdown("---")
if st.button("🚀 HITUNG RAB", type="primary", use_container_width=True):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=row['kode'],
        uraian_pekerjaan=row['uraian'],
        satuan=row['satuan'],
        volume=vol,
        harga_tenaga=h_tenaga, koefisien_tenaga=k_tenaga,
        harga_bahan=h_bahan, koefisien_bahan=k_bahan,
        harga_alat=h_alat, koefisien_alat=k_alat
    )
    
    # Tampilkan Tabel
    res_df = pd.DataFrame([hasil])
    st.dataframe(
        res_df[['uraian', 'volume', 'hsp_tenaga', 'hsp_bahan', 'hsp_alat', 'harga_satuan', 'total']],
        hide_index=True, use_container_width=True
    )
    st.success(f"TOTAL: Rp {hasil['total']:,.0f}")
