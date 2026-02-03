import streamlit as st
import pandas as pd
import os
import ast

# Import Universal Engine
try:
    from engine import sda_engine
except ImportError:
    st.error("🚨 Engine tidak ditemukan! Pastikan file sda_engine.py ada di folder engine/.")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Modul Bina Marga", page_icon="🛣️", layout="wide")
st.title("🛣️ Modul Bina Marga (Jalan & Jembatan)")
st.caption("Spesialisasi: Divisi 1-8 (Umum, Drainase, Tanah, Perkerasan, Struktur)")

# Session State untuk BOQ
if "boq_bm" not in st.session_state:
    st.session_state.boq_bm = []

# ==========================================
# 1. LOAD DATABASE (CSV Pattern)
# ==========================================
@st.cache_data
def load_db_bm():
    # Pastikan Anda sudah convert data Bina Marga dan simpan dengan nama ini
    path = "data/ahsp_binamarga_master.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            # Standarisasi kolom
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Gagal membaca database: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df_bm = load_db_bm()

# ==========================================
# 2. SIDEBAR: HARGA SATUAN DASAR
# ==========================================
st.sidebar.header("💰 Harga Dasar & Parameter")
uploaded_shs = st.sidebar.file_uploader("Upload SHS (Harga Satuan)", type=["xlsx", "csv"])

# Dictionary Harga (Default Kosong)
harga_db = {}

if uploaded_shs:
    try:
        if uploaded_shs.name.endswith('.csv'):
            df_harga = pd.read_csv(uploaded_shs)
        else:
            df_harga = pd.read_excel(uploaded_shs)
        
        # Asumsi kolom: 'nama', 'harga'
        # Bersihkan nama agar match (lowercase)
        harga_db = dict(zip(
            df_harga.iloc[:, 0].str.strip().str.lower(), 
            df_harga.iloc[:, 1]
        ))
        st.sidebar.success(f"✅ Terload: {len(harga_db)} item harga")
    except:
        st.sidebar.error("Format file harga salah.")

# Overhead Input
overhead_rate = st.sidebar.slider("Overhead & Profit (%)", 0, 15, 15)

# ==========================================
# 3. INTERFACE UTAMA
# ==========================================

if df_bm.empty:
    st.warning("⚠️ Database `data/ahsp_binamarga_master.csv` belum ditemukan.")
    st.info("Gunakan menu `converter.py` untuk membuat database dari file Excel/CSV mentah AHSP Bina Marga.")
else:
    # --- FILTERING ---
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        # Cari berdasarkan kode atau uraian
        search_kw = st.text_input("🔍 Cari Pekerjaan (Contoh: Lapis Pondasi / K.12)", "")
    
    if search_kw:
        df_display = df_bm[
            df_bm['uraian'].str.contains(search_kw, case=False, na=False) | 
            df_bm['kode'].str.contains(search_kw, case=False, na=False)
        ]
    else:
        df_display = df_bm.head(10) # Tampilkan 10 teratas jika belum cari

    # Pilih Item
    item_option = st.selectbox(
        "Pilih Analisa Pekerjaan:",
        options=df_display['kode'].tolist(),
        format_func=lambda x: f"{x} - {df_display[df_display['kode'] == x]['uraian'].values[0]}"
    )

    # Input Volume
    volume_input = st.number_input("Volume Pekerjaan", min_value=0.0, value=1.0, step=0.1)

    # --- PROSES PARSING KOEFISIEN ---
    # Fungsi bantu parsing string "Semen:10;Pasir:5" menjadi Dict
    def parse_koef_string(koef_str):
        if pd.isna(koef_str) or koef_str == "-": return {}
        try:
            # Format di converter.py: "Nama1:Koef1;Nama2:Koef2"
            items = str(koef_str).split(";")
            hasil = {}
            for item in items:
                if ":" in item:
                    nama, nilai = item.rsplit(":", 1)
                    hasil[nama.strip()] = float(nilai)
            return hasil
        except:
            return {}

    # Ambil data baris terpilih
    row = df_bm[df_bm['kode'] == item_option].iloc[0]
    
    koef_tenaga = parse_koef_string(row.get('tenaga', ''))
    koef_bahan = parse_koef_string(row.get('bahan', ''))
    koef_alat = parse_koef_string(row.get('alat', ''))

    # Tombol Hitung
    if st.button("➕ Tambahkan ke RAB Jalan"):
        # Mapping Harga (Case Insensitive Matching)
        def get_harga_match(nama_item):
            key = nama_item.lower().strip()
            return harga_db.get(key, 0) # Default 0 jika harga tidak ada

        # Siapkan Dict Harga
        h_tenaga = {k: get_harga_match(k) for k in koef_tenaga}
        h_bahan = {k: get_harga_match(k) for k in koef_bahan}
        h_alat = {k: get_harga_match(k) for k in koef_alat}

        # Panggil Engine
        hasil = sda_engine.hitung_rab_lengkap(
            kode_ahsp=row['kode'],
            uraian=row['uraian'],
            volume=volume_input,
            satuan=row['satuan'],
            koef_tenaga=koef_tenaga, harga_tenaga=h_tenaga,
            koef_bahan=koef_bahan, harga_bahan=h_bahan,
            koef_alat=koef_alat, harga_alat=h_alat,
            persen_overhead=overhead_rate
        )
        
        st.session_state.boq_bm.append(hasil)
        st.success("Item berhasil ditambahkan!")

# ==========================================
# 4. TAMPILAN TABEL BOQ (OUTPUT)
# ==========================================
st.divider()
st.subheader("📋 Rencana Anggaran Biaya (Bina Marga)")

if st.session_state.boq_bm:
    # Flatten data untuk tabel
    list_view = []
    for item in st.session_state.boq_bm:
        list_view.append({
            "kode_ahsp": item['meta']['kode'],
            "uraian": item['meta']['uraian'],
            "volume": item['meta']['volume'],
            "satuan": item['meta']['satuan'],
            "harga_satuan": item['biaya']['hsp'],
            "total": item['biaya']['total_final'],
            "komponen_alat": item['biaya']['alat'] # Info penting utk BM
        })
    
    df_view = pd.DataFrame(list_view)
    
    # Tampilkan Dataframe
    st.dataframe(
        df_view,
        column_config={
            "harga_satuan": st.column_config.NumberColumn("HSP (Rp)", format="Rp %.0f"),
            "total": st.column_config.NumberColumn("Total (Rp)", format="Rp %.0f"),
            "komponen_alat": st.column_config.NumberColumn("Biaya Alat", format="Rp %.0f"),
        },
        use_container_width=True
    )
    
    # Total Grand
    grand_total = df_view['total'].sum()
    st.markdown(f"### 💰 Total Proyek: **Rp {grand_total:,.0f}**")

    # Tombol Download Excel
    xlsx_data = sda_engine.export_to_excel(df_view)
    st.download_button(
        label="📥 Download RAB Excel",
        data=xlsx_data,
        file_name="RAB_Bina_Marga_2025.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Belum ada item pekerjaan. Silakan pilih di atas.")
