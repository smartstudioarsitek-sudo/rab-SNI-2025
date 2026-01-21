import streamlit as st
import pandas as pd
import sys
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Modul SDA (CSV Mode)", layout="wide")

# Import Engine
sys.path.append('.')
try:
    from engine import sda_engine
except:
    st.error("Engine tidak ditemukan.")
    st.stop()

st.title("🌊 Modul SDA (Versi Ringan CSV)")
st.caption("Anti-Ribet: Upload CSV Database & CSV Harga")

# ==========================================
# 1. SIDEBAR: UPLOAD FILE
# ==========================================
st.sidebar.header("📂 1. Upload Database")

# A. Upload AHSP (Resep)
file_ahsp = st.sidebar.file_uploader("Upload ahsp.csv", type=["csv"])
df_ahsp = pd.DataFrame()

if file_ahsp:
    try:
        df_ahsp = pd.read_csv(file_ahsp)
        # Bersihkan nama kolom
        df_ahsp.columns = [c.strip().lower() for c in df_ahsp.columns]
        st.sidebar.success(f"✅ {len(df_ahsp)} Item AHSP dimuat")
    except Exception as e:
        st.sidebar.error(f"Error CSV: {e}")

# B. Upload Harga (Toko)
st.sidebar.markdown("---")
st.sidebar.header("💰 2. Upload Harga")
file_harga = st.sidebar.file_uploader("Upload harga.csv", type=["csv"])
dict_harga = {}

if file_harga:
    try:
        df_harga = pd.read_csv(file_harga)
        df_harga.columns = [c.strip().lower() for c in df_harga.columns]
        
        # Buat Dictionary: {"semen": 1500}
        # Kita pakai huruf kecil semua biar pasti ketemu
        if 'nama' in df_harga.columns and 'harga' in df_harga.columns:
            dict_harga = dict(zip(
                df_harga['nama'].astype(str).str.lower().str.strip(),
                df_harga['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Harga dimuat")
            
            # Debug: Tampilkan apa yang dibaca
            with st.sidebar.expander("Cek Harga Terbaca"):
                st.write(dict_harga)
        else:
            st.sidebar.error("CSV Harga harus punya kolom 'nama' dan 'harga'")
            
    except Exception as e:
        st.sidebar.error(f"Error Harga: {e}")

# ==========================================
# 2. PROSES MATCHING & HITUNG
# ==========================================
if df_ahsp.empty:
    st.info("👈 Silakan upload file 'ahsp.csv' dulu di sidebar.")
    st.stop()

st.divider()

# Pilih Pekerjaan
kode = st.selectbox("Pilih Pekerjaan:", df_ahsp['kode'].astype(str) + " - " + df_ahsp['uraian'])
# Ambil baris data
row = df_ahsp[df_ahsp['kode'] == kode.split(" - ")[0]].iloc[0]

st.subheader(f"Analisa: {row['uraian']}")
vol = st.number_input(f"Volume ({row['satuan']})", value=1.0)

# --- FUNGSI PARSING KOEFISIEN ---
def parse_and_price(text_koef):
    """
    Mengubah teks "Semen 300; Pasir 0.5" menjadi Dictionary Input Harga
    """
    input_vals = {}
    koef_vals = {}
    
    if pd.isna(text_koef) or str(text_koef).strip() == "-":
        return {}, {}

    # Pisahkan berdasarkan titik koma
    items = str(text_koef).split(';')
    
    for item in items:
        # Regex simple: Ambil Nama (huruf) dan Angka
        import re
        # Pola: Ambil apa saja diawal, lalu angka di akhir
        # Contoh: "Semen 300" -> Nama="Semen", Angka=300
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        
        if match:
            nama_asli = match.group(1).strip()
            angka_koef = float(match.group(2))
            
            koef_vals[nama_asli] = angka_koef
            
            # CARI HARGA OTOMATIS
            # Kunci pencarian: huruf kecil
            kunci = nama_asli.lower()
            
            # Cek di kamus harga
            harga_dapat = 0.0
            if kunci in dict_harga:
                harga_dapat = float(dict_harga[kunci])
            else:
                # Coba cari mirip-mirip (partial match)
                for k_csv, v_csv in dict_harga.items():
                    if k_csv in kunci or kunci in k_csv:
                        harga_dapat = float(v_csv)
                        break
            
            # Tampilkan Input
            input_vals[nama_asli] = st.number_input(
                f"Harga {nama_asli}", 
                value=harga_dapat,
                step=100.0,
                key=f"input_{nama_asli}" # Key unik biar gak error
            )
            
            if harga_dapat > 0:
                st.caption(f"✅ Auto: Rp {harga_dapat:,.0f}")
            else:
                st.caption(f"❌ Tidak ketemu di CSV Harga")
                
    return input_vals, koef_vals

# Tampilkan Form 3 Kolom
col1, col2, col3 = st.columns(3)

with col1:
    st.info("👷 TENAGA")
    h_tenaga, k_tenaga = parse_and_price(row['tenaga'])

with col2:
    st.warning("🧱 BAHAN")
    h_bahan, k_bahan = parse_and_price(row['bahan'])

with col3:
    st.success("🚜 ALAT")
    h_alat, k_alat = parse_and_price(row['alat'])

# ==========================================
# 3. TOMBOL HITUNG
# ==========================================
st.markdown("---")
if st.button("🚀 HITUNG RAB SEKARANG", type="primary", use_container_width=True):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=row['kode'],
        uraian_pekerjaan=row['uraian'],
        satuan=row['satuan'],
        volume=vol,
        harga_tenaga=h_tenaga, koefisien_tenaga=k_tenaga,
        harga_bahan=h_bahan, koefisien_bahan=k_bahan,
        harga_alat=h_alat, koefisien_alat=k_alat
    )
    
    st.success("Perhitungan Selesai!")
    st.write("### 🧾 Rincian Biaya")
    
    res_df = pd.DataFrame([hasil])
    st.dataframe(res_df[['uraian', 'volume', 'hsp_tenaga', 'hsp_bahan', 'hsp_alat', 'harga_satuan', 'total']])
    
    st.metric("TOTAL HARGA", f"Rp {hasil['total']:,.0f}")
