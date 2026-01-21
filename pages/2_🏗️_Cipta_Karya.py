import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Modul Cipta Karya (Pro)", layout="wide")
st.title("🏗️ Modul Cipta Karya (Analisa Detail)")
st.caption("Menghitung RAB Gedung berdasarkan Koefisien (AHSP)")

if "rab_ck" not in st.session_state:
    st.session_state.rab_ck = []

# ==============================
# 1. LOAD DATABASE (Master CK yang sudah diconvert)
# ==============================
@st.cache_data
def load_ahsp_ck():
    path = "data/ahsp_ciptakarya_master.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, sep=None, engine='python')
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df_ahsp = load_ahsp_ck()

# ==============================
# 2. UPLOAD HARGA TOKO (SHS)
# ==============================
st.sidebar.header("1. Upload Harga Toko")
st.sidebar.caption("Upload Excel Harga (Semen, Cat, Upah, dll)")

file_harga = st.sidebar.file_uploader("Upload SHS Gedung", type=["xlsx", "csv"])
dict_harga = {}

if file_harga:
    try:
        if file_harga.name.endswith('.xlsx'):
            df_h = pd.read_excel(file_harga)
        else:
            df_h = pd.read_csv(file_harga, sep=None, engine='python')
            
        df_h.columns = [str(c).strip().lower() for c in df_h.columns]
        
        # Cari kolom Nama dan Harga secara pintar
        col_nama = None
        col_harga = None
        for col in df_h.columns:
            if any(x in col for x in ['nama', 'uraian', 'komponen']): col_nama = col
            if any(x in col for x in ['harga', 'price', 'rupiah']): col_harga = col
            
        if col_nama and col_harga:
            df_h = df_h.dropna(subset=[col_harga])
            df_h[col_nama] = df_h[col_nama].astype(str).str.replace('\n', ' ').str.strip().str.lower()
            dict_harga = dict(zip(df_h[col_nama], df_h[col_harga]))
            st.sidebar.success(f"✅ {len(dict_harga)} Item Harga Terbaca")
        else:
            st.sidebar.error("Gagal mendeteksi kolom Nama/Harga.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# ==============================
# 3. PILIH PEKERJAAN
# ==============================
if df_ahsp.empty:
    st.error("⚠️ Database Cipta Karya belum ada.")
    st.info("1. Buka menu 'Admin Converter'.")
    st.info("2. Upload file `data_rab.xlsx` pakai Mode 1 (SDA/Detail).")
    st.info("3. Rename hasilnya jadi `ahsp_ciptakarya_master.csv` dan upload ke folder `data/`.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("2. Input Pekerjaan")

# Filter agar hanya menampilkan yang punya Uraian
df_ahsp = df_ahsp.dropna(subset=['uraian'])
pilihan = st.sidebar.selectbox("Pilih Item:", df_ahsp['kode'].astype(str) + " | " + df_ahsp['uraian'])

kode = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode].iloc[0]

vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.01)

# ==============================
# 4. ENGINE HITUNG (Sama persis dengan SDA)
# ==============================
def cari_harga(nama_item):
    kunci = nama_item.lower().strip()
    if kunci in dict_harga: return float(dict_harga[kunci]), True
    for k, v in dict_harga.items():
        if k in kunci or kunci in k: return float(v), True
    return 0.0, False

def hitung_komponen(label, text_data):
    total = 0.0
    detail_html = ""
    if pd.isna(text_data) or str(text_data).strip() in ["-", "nan"]:
        return 0.0, "<small>- Tidak ada -</small>"

    for item in str(text_data).split(';'):
        import re
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        if match:
            nama = match.group(1).strip()
            koef = float(match.group(2))
            harga, ketemu = cari_harga(nama)
            subtotal = koef * harga
            total += subtotal
            warna = "green" if ketemu else "red"
            status = f"✅ {harga:,.0f}" if ketemu else "❌ 0"
            detail_html += f"<div style='border-bottom:1px solid #eee;'><b>{nama}</b> <span style='color:{warna}'>({status})</span><br>{koef} x {harga:,.0f} = <b>{subtotal:,.0f}</b></div>"
    return total, detail_html

st.subheader(f"Analisa: {row['uraian']}")
c1, c2, c3 = st.columns(3)

with c1: 
    st.info("Tenaga")
    t1, h1 = hitung_komponen("Tenaga", row.get('tenaga', '-'))
    st.markdown(h1, unsafe_allow_html=True)
    st.write(f"**Sub: {t1:,.0f}**")

with c2: 
    st.warning("Bahan")
    t2, h2 = hitung_komponen("Bahan", row.get('bahan', '-'))
    st.markdown(h2, unsafe_allow_html=True)
    st.write(f"**Sub: {t2:,.0f}**")

with c3: 
    st.success("Alat")
    t3, h3 = hitung_komponen("Alat", row.get('alat', '-'))
    st.markdown(h3, unsafe_allow_html=True)
    st.write(f"**Sub: {t3:,.0f}**")

# Rekap
jumlah_dasar = t1 + t2 + t3
overhead = jumlah_dasar * 0.15 # Standar Gedung biasanya 10-15%
hsp = jumlah_dasar + overhead
total_final = hsp * vol

st.divider()
kiri, kanan = st.columns([2, 1])

with kiri:
    st.write(f"HSP (Dasar + Overhead 15%): **Rp {hsp:,.2f}**")
    if jumlah_dasar == 0:
        st.error("⚠️ Harga masih 0. Upload file Harga (SHS) dulu di sidebar!")
        
with kanan:
    st.metric("TOTAL HARGA", f"Rp {total_final:,.0f}")
    if st.button("➕ Simpan ke RAB Gedung"):
        st.session_state.rab_ck.append({
            "Kode": kode, 
            "Uraian": row['uraian'], 
            "Vol": vol, 
            "Satuan": row['satuan'],
            "Total": total_final
        })
        st.success("Tersimpan!")

# Tabel RAB
if st.session_state.rab_ck:
    st.markdown("---")
    df_rab = pd.DataFrame(st.session_state.rab_ck)
    st.dataframe(df_rab, use_container_width=True)
    st.metric("GRAND TOTAL PROYEK", f"Rp {df_rab['Total'].sum():,.0f}")
    if st.button("Reset RAB"):
        st.session_state.rab_ck = []
        st.rerun()
