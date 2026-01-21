import streamlit as st
import pandas as pd
import os
import sys

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Modul SDA", layout="wide")
sys.path.append('.')

try:
    from engine import sda_engine
except ModuleNotFoundError:
    st.error("🚨 Modul engine tidak ditemukan.")
    st.stop()

st.title("🌊 Modul Sumber Daya Air (SDA)")

# ==============================
# 1. LOAD DATABASE AHSP (Excel)
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    if not os.path.exists(path):
        st.error("Database AHSP tidak ditemukan.")
        st.stop()
    try:
        xls = pd.ExcelFile(path)
        for sheet in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            if "kode_ahsp" in df.columns:
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df = load_database()

# ==============================
# 2. LOAD HARGA (CSV ONLY) ⚡
# ==============================
st.sidebar.header("📥 Upload Harga (CSV)")
st.sidebar.info("Gunakan format .csv (Notepad) agar lebih akurat.")

uploaded_file = st.sidebar.file_uploader("Upload file harga_lampung.csv", type=["csv"])

harga_dict = {} # Dictionary untuk menyimpan harga

if uploaded_file:
    try:
        # Baca CSV
        df_harga = pd.read_csv(uploaded_file)
        
        # Bersihkan nama kolom (biar huruf kecil semua)
        df_harga.columns = [c.strip().lower() for c in df_harga.columns]
        
        # Pastikan ada kolom 'nama' dan 'harga'
        if 'nama' in df_harga.columns and 'harga' in df_harga.columns:
            # Buat Dictionary { "semen (pc)" : 1850 }
            # Kita kecilkan hurufnya (lower) biar tidak masalah kapitalisasi
            harga_dict = dict(zip(
                df_harga['nama'].astype(str).str.lower().str.strip(),
                df_harga['harga']
            ))
            st.sidebar.success(f"✅ Berhasil muat {len(harga_dict)} harga!")
            
            # Tampilkan Tabel Preview Kecil
            with st.sidebar.expander("Lihat Data CSV"):
                st.dataframe(df_harga, hide_index=True)
        else:
            st.sidebar.error("❌ Format CSV Salah! Harus ada kolom 'nama' dan 'harga'.")
    except Exception as e:
        st.sidebar.error(f"Gagal baca CSV: {e}")

# ==============================
# 3. ANALISA & MATCHING
# ==============================
st.sidebar.markdown("---")
st.sidebar.header("🛠️ Hitung Item")

if df.empty:
    st.warning("Database AHSP kosong.")
    st.stop()

kode_terpilih = st.sidebar.selectbox("Pilih Pekerjaan:", df["kode_ahsp"].astype(str).tolist())
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

st.info(f"**{row['uraian_pekerjaan']}** (Satuan: {row['satuan']})")
volume = st.number_input("Volume", value=1.0)

# Helper Parsing
def parse_koef(text):
    res = {}
    if pd.isna(text) or str(text) == "-": return res
    for part in str(text).split(';'):
        try:
            # Regex ambil Nama dan Angka
            import re
            m = re.search(r'^(.*?)\s+([\d\.]+)', part.strip())
            if m: res[m.group(1).strip()] = float(m.group(2))
        except: pass
    return res

koef_tenaga = parse_koef(row.get('tenaga_detail', '-'))
koef_bahan = parse_koef(row.get('bahan_detail', '-'))
koef_alat = parse_koef(row.get('alat_detail', '-'))

# --- FUNGSI CARI HARGA (EXACT MATCH) ---
def cari_harga(nama_item):
    key = nama_item.lower().strip()
    
    # 1. Cari Persis
    if key in harga_dict:
        return float(harga_dict[key])
    
    # 2. Cari Mirip (Backup)
    # Misal: di DB "Pasir Beton", di CSV "Pasir".
    for k, v in harga_dict.items():
        if k in key or key in k:
            return float(v)
            
    return 0.0

# Generate Input Form
input_tenaga = {}
input_bahan = {}
input_alat = {}

def buat_form(label, data_koef, input_dict):
    if data_koef:
        st.sidebar.subheader(label)
        for nama, koef in data_koef.items():
            # Cari harga otomatis
            harga_auto = cari_harga(nama)
            
            # Tampilkan input
            input_dict[nama] = st.sidebar.number_input(
                f"{nama}", 
                value=harga_auto,
                step=1000.0
            )
            # Indikator visual
            if harga_auto > 0:
                st.sidebar.caption(f"✅ Ditemukan: Rp {harga_auto:,.0f}")
            else:
                st.sidebar.caption(f"❌ Tidak ada di CSV (Isi manual)")

buat_form("👷 Tenaga", koef_tenaga, input_tenaga)
buat_form("🧱 Bahan", koef_bahan, input_bahan)
buat_form("🚜 Alat", koef_alat, input_alat)

# ==============================
# 4. EKSEKUSI
# ==============================
if st.button("🚀 Hitung RAB", type="primary"):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=kode_terpilih,
        uraian_pekerjaan=row['uraian_pekerjaan'],
        satuan=row['satuan'],
        volume=volume,
        harga_tenaga=input_tenaga, koefisien_tenaga=koef_tenaga,
        harga_bahan=input_bahan, koefisien_bahan=koef_bahan,
        harga_alat=input_alat, koefisien_alat=koef_alat
    )
    if "boq" not in st.session_state: st.session_state.boq = []
    st.session_state.boq.append(hasil)
    st.success("Sukses!")

# Tampilkan Tabel
if "boq" in st.session_state and st.session_state.boq:
    st.dataframe(pd.DataFrame(st.session_state.boq))
