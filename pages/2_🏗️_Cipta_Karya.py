import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Modul Cipta Karya", layout="wide")
st.title("🏗️ Modul Cipta Karya (Gedung)")

if "rab_ck" not in st.session_state: st.session_state.rab_ck = []

@st.cache_data
def load_data_ck():
    path = "data/ahsp_ciptakarya_master.csv"
    if not os.path.exists(path): return pd.DataFrame()
    try:
        df = pd.read_csv(path, sep=None, engine='python')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.dropna(subset=['uraian'])
        df['kode'] = df['kode'].astype(str)
        return df
    except: return pd.DataFrame()

df_ck = load_data_ck()

# ==============================
# 1. UPLOAD HARGA (FORMAT FLEXIBLE)
# ==============================
st.sidebar.header("1. Upload Standar Harga")
st.sidebar.caption("Daftar Harga Satuan Jadi (Excel/CSV)")
file_harga = st.sidebar.file_uploader("Upload SHS Gedung", type=["xlsx", "csv"])

dict_harga_jadi = {}

if file_harga:
    try:
        if file_harga.name.endswith('.xlsx'):
            df_h = pd.read_excel(file_harga)
        else:
            df_h = pd.read_csv(file_harga, sep=None, engine='python')
            
        df_h.columns = [str(c).strip().lower() for c in df_h.columns]
        
        # LOGIKA PENCARIAN KOLOM PINTAR
        col_nama = None
        col_harga = None
        for col in df_h.columns:
            if any(x in col for x in ['nama', 'uraian', 'pekerjaan']): col_nama = col
            if any(x in col for x in ['harga', 'price', 'rp']): col_harga = col
        
        if col_nama and col_harga:
            df_h = df_h.dropna(subset=[col_harga])
            # Bersihkan nama (hapus enter)
            df_h[col_nama] = df_h[col_nama].astype(str).str.replace('\n', ' ').str.strip().str.lower()
            
            dict_harga_jadi = dict(zip(
                df_h[col_nama],
                df_h[col_harga]
            ))
            st.sidebar.success(f"✅ {len(dict_harga_jadi)} Harga Jadi Terbaca!")
        else:
            st.sidebar.error("Kolom Nama/Harga tidak ditemukan.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# ==============================
# INPUT USER
# ==============================
st.sidebar.markdown("---")
if df_ck.empty:
    st.error("Database Kosong. Lakukan konversi dulu.")
    st.stop()

pilihan = st.sidebar.selectbox("Cari Pekerjaan:", df_ck['kode'] + " | " + df_ck['uraian'])
kode = pilihan.split(" | ")[0]
row_df = df_ck[df_ck['kode'] == kode]

if not row_df.empty:
    row = row_df.iloc[0]
    st.sidebar.markdown("---")
    vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0)

    # ==============================
    # AUTO-MATCHING
    # ==============================
    st.subheader(f"Analisa: {row['uraian']}")
    harga_auto = 0.0
    kunci_cari = str(row['uraian']).lower().strip()

    # Cari harga
    if kunci_cari in dict_harga_jadi:
        harga_auto = float(dict_harga_jadi[kunci_cari])
    elif dict_harga_jadi:
        # Cari yang mirip
        for k, v in dict_harga_jadi.items():
            if k in kunci_cari: 
                harga_auto = float(v)
                break

    col1, col2 = st.columns([1, 2])
    with col1:
        harga_satuan = st.number_input("Harga Satuan (Rp)", value=harga_auto, step=5000.0)
        if harga_auto > 0: st.caption("✅ Ketemu di Excel!")
    
    with col2:
        total = harga_satuan * vol
        st.metric("TOTAL", f"Rp {total:,.0f}")
        if st.button("➕ Tambah"):
            st.session_state.rab_ck.append({"Kode":kode, "Uraian":row['uraian'], "Vol":vol, "Total":total})
            st.success("Masuk!")

    # TABEL BAWAH
    if st.session_state.rab_ck:
        st.divider()
        df_rab = pd.DataFrame(st.session_state.rab_ck)
        st.dataframe(df_rab, use_container_width=True)
        st.metric("GRAND TOTAL", f"Rp {df_rab['Total'].sum():,.0f}")
        if st.button("Reset"): st.session_state.rab_ck = []; st.rerun()
else:
    st.error("Item tidak valid.")
