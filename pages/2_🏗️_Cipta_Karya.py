import streamlit as st
import pandas as pd
import os

# ==============================
# CONFIG & HEADER
# ==============================
st.set_page_config(page_title="Modul Cipta Karya", layout="wide")
st.title("🏗️ Modul Cipta Karya (Gedung & Perumahan)")
st.caption("Estimasi Biaya Berdasarkan Standar Harga Satuan Jadi (Per m'/m2/Unit)")

# Inisialisasi Keranjang RAB CK
if "rab_ck" not in st.session_state:
    st.session_state.rab_ck = []

# ==============================
# 1. LOAD DATABASE (Dari Hasil Converter)
# ==============================
@st.cache_data
def load_data_ck():
    # Pastikan nama filenya sesuai hasil download dari Converter tadi
    path = "data/ahsp_ciptakarya_master.csv"
    
    if not os.path.exists(path):
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(path, sep=None, engine='python')
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_ck = load_data_ck()

# ==============================
# 2. INPUT PEKERJAAN (SIDEBAR)
# ==============================
st.sidebar.header("🛠️ Input Item Pekerjaan")

if df_ck.empty:
    st.error("⚠️ Database Cipta Karya belum ditemukan.")
    st.info("Lakukan konversi dulu di menu 'Admin Converter' (Pilih Mode 2), lalu upload hasilnya ke folder `data/`.")
    st.stop()

# Dropdown Pilihan (Searchable)
# Gabungkan Kode + Uraian biar gampang dicari
pilihan_label = df_ck['kode'].astype(str) + " | " + df_ck['uraian']
pilihan = st.sidebar.selectbox("Cari Pekerjaan:", options=pilihan_label)

# Ambil Data Baris Terpilih
kode_terpilih = pilihan.split(" | ")[0]
row = df_ck[df_ck['kode'] == kode_terpilih].iloc[0]

# Input Volume
st.sidebar.markdown("---")
vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.01)

# ==============================
# 3. ANALISA HARGA (SIMPLE MODE)
# ==============================
st.subheader(f"Analisa: {row['uraian']}")

# Coba cari harga di kolom 'tenaga' atau 'bahan' kalau-kalau ada angka terselip
# Tapi biasanya file CK yang tadi kosong, jadi kita input manual harganya.
st.info("ℹ️ Mode Harga Jadi: Masukkan harga satuan final sesuai kontrak/standar daerah.")

col1, col2 = st.columns([1, 2])

with col1:
    # Input Harga Satuan Manual (Karena di CSV tadi tidak ada kolom harga numeric)
    # Default 0, User harus isi sesuai standar harga setempat
    harga_satuan = st.number_input(
        "Harga Satuan (Rp)", 
        value=0.0, 
        step=10000.0, 
        help="Masukkan harga satuan jadi per m2/unit"
    )

with col2:
    # Tampilkan Total
    total_harga = harga_satuan * vol
    st.metric("TOTAL HARGA ITEM", f"Rp {total_harga:,.0f}")
    
    # Tombol Tambah
    if st.button("➕ Tambah ke RAB Gedung", type="primary"):
        if total_harga > 0:
            st.session_state.rab_ck.append({
                "Kode": row['kode'],
                "Uraian": row['uraian'],
                "Volume": vol,
                "Satuan": row['satuan'],
                "Harga Satuan": harga_satuan,
                "Total": total_harga
            })
            st.success("Item berhasil ditambahkan! 👇")
        else:
            st.warning("Harga masih 0. Mohon isi harga satuan dulu.")

# ==============================
# 4. TABEL REKAP RAB (BOQ)
# ==============================
st.divider()
st.header("📋 Bill of Quantities (BoQ) - Cipta Karya")

if st.session_state.rab_ck:
    df_rab = pd.DataFrame(st.session_state.rab_ck)
    
    # Tampilkan Tabel Rapi
    st.dataframe(
        df_rab, 
        use_container_width=True,
        column_config={
            "Harga Satuan": st.column_config.NumberColumn(format="Rp %.2f"),
            "Total": st.column_config.NumberColumn(format="Rp %.2f")
        }
    )
    
    # Grand Total
    grand_total = df_rab['Total'].sum()
    st.metric("GRAND TOTAL PROYEK GEDUNG", f"Rp {grand_total:,.0f}")
    
    # Tombol Hapus
    if st.button("🗑️ Reset RAB Gedung"):
        st.session_state.rab_ck = []
        st.rerun()
else:
    st.info("Belum ada item pekerjaan gedung yang ditambahkan.")
