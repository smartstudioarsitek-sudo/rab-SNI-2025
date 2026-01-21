import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Modul SDA (Final)", layout="wide")
st.title("🌊 Modul SDA (Penyusunan RAB)")

if "rab_list" not in st.session_state:
    st.session_state.rab_list = []

# --- LOAD DATABASE ---
@st.cache_data
def load_ahsp():
    path = "data/ahsp_sda_master.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, sep=None, engine='python')
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df_ahsp = load_ahsp()

# ==============================
# 1. UPLOAD HARGA (FORMAT KAKAK)
# ==============================
st.sidebar.header("1. Upload Daftar Harga")
st.sidebar.caption("Format: Nama Bahan & Harga (Excel/CSV)")

file_harga = st.sidebar.file_uploader("Upload SHS", type=["xlsx", "csv"])
dict_harga = {}

if file_harga:
    try:
        # 1. Baca File
        if file_harga.name.endswith('.xlsx'):
            df_h = pd.read_excel(file_harga)
        else:
            df_h = pd.read_csv(file_harga, sep=None, engine='python')
            
        # 2. Bersihkan Header (Huruf kecil semua)
        df_h.columns = [str(c).strip().lower() for c in df_h.columns]
        
        # 3. Cari Kolom NAMA dan HARGA secara Pintar
        col_nama = None
        col_harga = None
        
        for col in df_h.columns:
            if "nama" in col or "uraian" in col or "komponen" in col:
                col_nama = col
            if "harga" in col or "price" in col or "rupiah" in col:
                col_harga = col
        
        # 4. Proses Jika Kolom Ketemu
        if col_nama and col_harga:
            # Buang baris yang harganya kosong (biasanya baris Judul Kategori)
            df_h = df_h.dropna(subset=[col_harga])
            
            # Bersihkan Nama (Hapus Enter '\n' dan spasi)
            df_h[col_nama] = df_h[col_nama].astype(str).str.replace('\n', ' ').str.strip().str.lower()
            
            # Buat Kamus Harga
            dict_harga = dict(zip(
                df_h[col_nama],
                df_h[col_harga]
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Item Harga Terbaca!")
            
            # Preview (Opsional)
            with st.sidebar.expander("Cek Sampel Data"):
                st.write(df_h[[col_nama, col_harga]].head(5))
        else:
            st.sidebar.error(f"❌ Kolom tidak dikenali. Pastikan ada kata 'Nama' dan 'Harga' di header Excel.")
            st.sidebar.write("Header terbaca:", df_h.columns.tolist())
            
    except Exception as e:
        st.sidebar.error(f"Error baca file: {e}")

# ==============================
# LOGIKA PROGRAM (TETAP SAMA)
# ==============================
if df_ahsp.empty:
    st.error("Database AHSP belum ada (ahsp_sda_master.csv).")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("2. Input Pekerjaan")

pilihan = st.sidebar.selectbox("Pilih Item:", df_ahsp['kode'] + " | " + df_ahsp['uraian'])
kode = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode].iloc[0]

vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.1)

def cari_harga(nama_item):
    kunci = nama_item.lower().strip()
    # 1. Cari Persis
    if kunci in dict_harga: return float(dict_harga[kunci]), True
    # 2. Cari Mirip
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
    st.info("Tenaga"); t1, h1 = hitung_komponen("Tenaga", row.get('tenaga', '-')); st.markdown(h1, unsafe_allow_html=True); st.write(f"**Sub: {t1:,.0f}**")
with c2: 
    st.warning("Bahan"); t2, h2 = hitung_komponen("Bahan", row.get('bahan', '-')); st.markdown(h2, unsafe_allow_html=True); st.write(f"**Sub: {t2:,.0f}**")
with c3: 
    st.success("Alat"); t3, h3 = hitung_komponen("Alat", row.get('alat', '-')); st.markdown(h3, unsafe_allow_html=True); st.write(f"**Sub: {t3:,.0f}**")

jumlah = t1 + t2 + t3
oh = jumlah * 0.15
total = (jumlah + oh) * vol

st.divider()
kiri, kanan = st.columns([2,1])
with kiri: st.write(f"HSP (Dasar+15%): **Rp {(jumlah+oh):,.2f}**")
with kanan:
    st.metric("TOTAL", f"Rp {total:,.0f}")
    if st.button("➕ Simpan ke RAB"):
        st.session_state.rab_list.append({"Kode":kode, "Uraian":row['uraian'], "Vol":vol, "Total":total})
        st.success("Tersimpan!")

if st.session_state.rab_list:
    st.markdown("---")
    df_rab = pd.DataFrame(st.session_state.rab_list)
    st.dataframe(df_rab, use_container_width=True)
    st.metric("GRAND TOTAL", f"Rp {df_rab['Total'].sum():,.0f}")
    if st.button("Reset"): st.session_state.rab_list = []; st.rerun()
