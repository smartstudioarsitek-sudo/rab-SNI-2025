"""
UI STREAMLIT – APLIKASI RAB SDA
Phase 1 (Core)
Fitur:
- Multi-item BOQ
- Rekap RAB
- AHSP SDA 2025 (Tanah Manual)
- Engine deterministik
"""

import streamlit as st
import pandas as pd
from engine import sda_engine

st.set_page_config(page_title="RAB SDA 2025", layout="wide")

st.title("Aplikasi RAB SDA 2025 – Phase 1 (Core)")
st.caption("Berbasis AHSP SDA 2025 | BOQ & Rekap | Audit-safe")

# ==============================
# LOAD DATABASE AHSP
# ==============================
@st.cache_data
def load_ahsp():
    return pd.read_excel(
        "data/ahsp_sda_2025_tanah_manual_core.xlsx",
        sheet_name="ahsp_tanah_manual_core"
    )

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

row = df[df["kode_ahsp"] == kode_terpilih].iloc[0]

volume = st.sidebar.number_input(
    f"Volume ({row['satuan']})",
    min_value=0.0,
    value=1.0
)

st.sidebar.subheader("Harga Tenaga Kerja")
harga_pekerja = st.sidebar.number_input("Upah Pekerja (L.01)", value=120000)
harga_mandor = st.sidebar.number_input("Upah Mandor (L.04)", value=180000)

harga_tenaga = {
    "Pekerja (L.01)": harga_pekerja,
    "Mandor (L.04)": harga_mandor,
}

if st.sidebar.button("Tambah ke BOQ"):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=kode_terpilih,
        volume=volume,
        harga_tenaga=harga_tenaga
    )
    st.session_state.boq.append(hasil)
    st.sidebar.success("Item ditambahkan ke BOQ")

# ==============================
# TAMPILKAN BOQ
# ==============================
st.subheader("BOQ – Daftar Pekerjaan")

if st.session_state.boq:
    boq_df = pd.DataFrame(st.session_state.boq)
    st.dataframe(boq_df[[
        "kode_ahsp",
        "uraian",
        "satuan",
        "volume",
        "harga_satuan",
        "total",
    ]])

    # ==============================
    # REKAP RAB
    # ==============================
    st.subheader("Rekap RAB")
    total_rab = boq_df["total"].sum()
    st.metric("TOTAL RAB", f"Rp {total_rab:,.0f}")

    if st.button("Reset BOQ"):
        st.session_state.boq = []
        st.experimental_rerun()
else:
    st.info("BOQ masih kosong. Tambahkan item dari sidebar.")

# ==============================
# DETAIL AHSP TERPILIH
# ==============================
st.subheader("Detail AHSP Terpilih")
st.table(row[[
    "kode_ahsp",
    "uraian_pekerjaan",
    "metode",
    "satuan",
    "tenaga_detail",
    "catatan"
]])
