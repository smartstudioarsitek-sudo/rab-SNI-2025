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

st.title("🌊 Modul SDA (CSV Mode)")
st.caption("Solusi Akhir: Upload CSV Database & CSV Harga")

# ==========================================
# FUNGSI BACA CSV PINTAR (Auto-Detect Separator)
# ==========================================
def smart_read_csv(uploaded_file):
    try:
        # Coba baca pakai KOMA (Default)
        df = pd.read_csv(uploaded_file)
        
        # Kalau kolomnya cuma 1 (berarti gagal pisah), coba pakai TITIK KOMA
        if len(df.columns) < 2:
            uploaded_file.seek(0) # Reset file pointer
            df = pd.read_csv(uploaded_file, sep=';')
            
        # Bersihkan nama kolom (huruf kecil, hapus spasi)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 1. SIDEBAR: UPLOAD FILE
# ==========================================
st.sidebar.header("📂 1. Upload Database AHSP")
file_ahsp = st.sidebar.file_uploader("Upload ahsp.csv", type=["csv"])
df_ahsp = pd.DataFrame()

if file_ahsp:
    df, err = smart_read_csv(file_ahsp)
    if err:
        st.sidebar.error(f"Error: {err}")
    else:
        # Validasi kolom wajib
        if 'kode' in df.columns and 'uraian' in df.columns:
            df_ahsp = df
            st.sidebar.success(f"✅ {len(df_ahsp)} Item AHSP Masuk")
            # TAMPILKAN HASIL BACA (DEBUG)
            with st.sidebar.expander("👁️ Cek Data AHSP"):
                st.dataframe(df_ahsp.head(3))
        else:
            st.sidebar.error("❌ CSV Salah! Wajib ada kolom: kode, uraian, satuan, tenaga, bahan, alat")

st.sidebar.markdown("---")
st.sidebar.header("💰 2. Upload Harga Satuan")
file_harga = st.sidebar.file_uploader("Upload harga.csv", type=["csv"])
dict_harga = {}

if file_harga:
    df_h, err_h = smart_read_csv(file_harga)
    if err_h:
        st.sidebar.error(f"Error: {err_h}")
    else:
        if 'nama' in df_h.columns and 'harga' in df_h.columns:
            # Buat Dictionary Harga
            dict_harga = dict(zip(
                df_h['nama'].astype(str).str.lower().str.strip(),
                df_h['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Harga Masuk")
            
            # TAMPILKAN HASIL BACA (DEBUG)
            with st.sidebar.expander("👁️ Cek Data Harga"):
                st.dataframe(df_h.head(3))
        else:
            st.sidebar.error("❌ CSV Salah! Wajib ada kolom: nama, harga")

# ==========================================
# 2. PROSES MATCHING & HITUNG
# ==========================================
if df_ahsp.empty:
    st.info("👈 Silakan upload file 'ahsp.csv' dulu di sidebar.")
    st.stop()

st.divider()

# Pilih Pekerjaan
# Gabungkan Kode + Uraian biar gampang milihnya
pilihan_label = df_ahsp['kode'].astype(str) + " | " + df_ahsp['uraian']
pilihan = st.selectbox("Pilih Pekerjaan:", options=pilihan_label)

# Ambil Kode dari pilihan (split berdasarkan garis tegak |)
kode_terpilih = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode_terpilih].iloc[0]

st.subheader(f"Analisa: {row['uraian']}")
col_vol, col_dummy = st.columns([1, 3])
with col_vol:
    vol = st.number_input(f"Volume ({row['satuan']})", value=1.0)

# --- FUNGSI PARSING & PRICING ---
def process_resources(text_koef):
    """
    Mengubah teks "Semen 300; Pasir 0.5" menjadi Dictionary Input
    """
    input_vals = {}
    koef_vals = {}
    
    if pd.isna(text_koef) or str(text_koef).strip() in ["-", "nan"]:
        return {}, {}

    # Pisah titik koma (;)
    items = str(text_koef).split(';')
    
    for item in items:
        # Regex: Ambil Nama (huruf) dan Angka
        import re
        # Pola: Nama di depan, Angka di belakang/tengah
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        
        if match:
            nama_asli = match.group(1).strip()
            angka_koef = float(match.group(2))
            
            koef_vals[nama_asli] = angka_koef
            
            # CARI HARGA (Logic Super Loose)
            kunci = nama_asli.lower()
            harga_dapat = 0.0
            
            # 1. Cari Exact Match
            if kunci in dict_harga:
                harga_dapat = float(dict_harga[kunci])
            else:
                # 2. Cari Partial Match (Mirip)
                for k_csv, v_csv in dict_harga.items():
                    # Apakah "semen" ada di "semen gresik"? YA.
                    if k_csv in kunci or kunci in k_csv:
                        harga_dapat = float(v_csv)
                        break
            
            # Input Form
            input_vals[nama_asli] = st.number_input(
                f"Harga {nama_asli}", 
                value=harga_dapat,
                step=100.0,
                key=f"{kode_terpilih}_{nama_asli}" # Key unik
            )
            
            if harga_dapat > 0:
                st.caption(f"✅ Auto: Rp {harga_dapat:,.0f}")
            else:
                st.caption(f"❌ Tidak ada di CSV Harga")
                
    return input_vals, koef_vals

# Tampilkan Form 3 Kolom
col1, col2, col3 = st.columns(3)

with col1:
    st.info("👷 TENAGA")
    h_tenaga, k_tenaga = process_resources(row.get('tenaga', '-'))

with col2:
    st.warning("🧱 BAHAN")
    h_bahan, k_bahan = process_resources(row.get('bahan', '-'))

with col3:
    st.success("🚜 ALAT")
    h_alat, k_alat = process_resources(row.get('alat', '-'))

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
    
    # Tampilkan Hasil Ringkas
    res_df = pd.DataFrame([hasil])
    st.dataframe(
        res_df[['uraian', 'volume', 'hsp_tenaga', 'hsp_bahan', 'hsp_alat', 'harga_satuan', 'total']],
        hide_index=True,
        use_container_width=True
    )
    
    st.metric("TOTAL HARGA", f"Rp {hasil['total']:,.0f}")
