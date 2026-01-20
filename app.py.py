# File: app.py

import streamlit as st
import pandas as pd
import os

# Import engine yang sudah kita buat
try:
    from engine import sda_engine
except ModuleNotFoundError:
    st.error("Modul 'engine' tidak ditemukan. Pastikan folder 'engine' dan file 'sda_engine.py' sudah dibuat.")
    st.stop()

st.set_page_config(page_title="RAB SDA 2025", layout="wide")

st.title("Aplikasi RAB SDA 2025 – Phase 1 (Core)")
st.caption("Berbasis AHSP SDA 2025 | BOQ & Rekap | Audit-safe")

# ==============================
# LOAD DATABASE AHSP
# ==============================
@st.cache_data
def load_ahsp():
    path = "data/ahsp_sda_2025_tanah_manual_core.xlsx"
    
    # Cek apakah file ada, jika tidak gunakan Data Dummy untuk demo
    if not os.path.exists(path):
        st.warning(f"File database '{path}' tidak ditemukan. Menggunakan data dummy.")
        data_dummy = {
            "kode_ahsp": ["T.01.a", "T.02.b"],
            "uraian_pekerjaan": ["Galian Tanah Biasa sedalam < 1 m", "Timbunan Tanah Kembali"],
            "satuan": ["m3", "m3"],
            "metode": ["Manual", "Manual"],
            "tenaga_detail": ["Pekerja (L.01);Mandor (L.04)", "Pekerja (L.01);Mandor (L.04)"],
            "catatan": ["-", "-"],
            # Koefisien disimpan sbg JSON atau kolom terpisah di Excel asli
            # Di sini kita simpan hardcode untuk contoh
            "koef_pekerja": [0.750, 0.500], 
            "koef_mandor": [0.025, 0.050]
        }
        return pd.DataFrame(data_dummy)

    return pd.read_excel(path, sheet_name="ahsp_tanah_manual_core")

df = load_ahsp()

# ==============================
# SESSION STATE: BOQ
# ==============================
if "boq" not in st.session_state:
    st.session_state.boq = []

# ==============================
# SIDEBAR INPUT
# ==============================
st.sidebar.header("Tambah Item BOQ")

kode_list = df["kode_ahsp"].tolist()
kode_terpilih = st.sidebar.selectbox("Kode AHSP", kode_list)

# Ambil baris data berdasarkan kode
row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

volume = st.sidebar.number_input(
    f"Volume ({row['satuan']})",
    min_value=0.0,
    value=1.0,
    step=0.1
)

st.sidebar.subheader("Harga Tenaga Kerja (Rp/Hari)")
harga_pekerja = st.sidebar.number_input("Upah Pekerja (L.01)", value=120000, step=5000)
harga_mandor = st.sidebar.number_input("Upah Mandor (L.04)", value=180000, step=5000)

harga_tenaga = {
    "Pekerja (L.01)": harga_pekerja,
    "Mandor (L.04)": harga_mandor,
}

# --- LOGIC EXTRACTION KOEFISIEN ---
# Asumsi: Di Excel kamu ada kolom 'koef_pekerja' dan 'koef_mandor'
# Jika struktur excel beda, sesuaikan bagian ini.
koefisien_tenaga = {
    "Pekerja (L.01)": row.get("koef_pekerja", 0), # Default 0 jika kolom tak ada
    "Mandor (L.04)": row.get("koef_mandor", 0),
}

if st.sidebar.button("Tambah ke BOQ"):
    # Panggil fungsi hitung dari Engine
    hasil = sda_engine.hitung_rab(
        kode_ahsp=kode_terpilih,
        volume=volume,
        harga_tenaga=harga_tenaga,
        koefisien_tenaga=koefisien_tenaga, # Passing koefisien
        uraian_pekerjaan=row["uraian_pekerjaan"], # Passing nama
        satuan=row["satuan"]
    )
    st.session_state.boq.append(hasil)
    st.sidebar.success("Item ditambahkan ke BOQ")

# ==============================
# TAMPILKAN BOQ
# ==============================
st.subheader("BOQ – Daftar Pekerjaan")

if st.session_state.boq:
    boq_df = pd.DataFrame(st.session_state.boq)
    
    # Format tabel agar angka lebih rapi
    st.dataframe(
        boq_df,
        column_config={
            "harga_satuan": st.column_config.NumberColumn("Harga Satuan", format="Rp %.0f"),
            "total": st.column_config.NumberColumn("Total Harga", format="Rp %.0f")
        },
        use_container_width=True
    )

    # ==============================
    # REKAP RAB
    # ==============================
    st.markdown("---")
    st.subheader("Rekap RAB")
    total_rab = boq_df["total"].sum()
    st.metric("TOTAL RAB KONSTRUKSI", f"Rp {total_rab:,.0f}")

    if st.button("Reset BOQ", type="primary"):
        st.session_state.boq = []
        st.rerun() # Updated from experimental_rerun
else:
    st.info("BOQ masih kosong. Silakan pilih item pekerjaan di sidebar kiri.")

# ==============================
# DETAIL AHSP TERPILIH
# ==============================
st.markdown("---")
st.subheader("Detail AHSP Reference")
st.json(row.to_dict()) # Tampilkan raw data untuk debug
