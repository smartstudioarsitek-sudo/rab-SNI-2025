"""
UI STREAMLIT – APLIKASI RAB SDA 2025
Phase 1 (Core)
Fitur:
- Multi-item BOQ
- Rekap RAB
- Input harga TENAGA, BAHAN, ALAT
- Engine deterministik (audit-safe)
"""

import streamlit as st
import pandas as pd
from engine import sda_engine


st.set_page_config(page_title="RAB SDA 2025", layout="wide")

st.title("Aplikasi RAB SDA 2025 – Phase 1 (Core)")
st.caption("AHSP SDA 2025 | BOQ & Rekap | Tenaga + Bahan + Alat")

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
# SESSION STATE
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

# ==============================
# HARGA TENAGA
# ==============================
st.sidebar.subheader("Harga Tenaga Kerja (Rp)")
harga_pekerja = st.sidebar.number_input("Upah Pekerja (L.01)", value=120000)
harga_mandor = st.sidebar.number_input("Upah Mandor (L.04)", value=180000)

harga_tenaga = {
    "Pekerja (L.01)": harga_pekerja,
    "Mandor (L.04)": harga_mandor,
}

# ==============================
# HARGA BAHAN
# ==============================
st.sidebar.subheader("Harga Bahan (Rp)")
harga_bahan = {}

if isinstance(row["bahan_detail"], str) and row["bahan_detail"] not in ["", "-"]:
    bahan_list = [b.strip().rsplit(" ", 1)[0] for b in row["bahan_detail"].split(";")]
    for b in bahan_list:
        harga_bahan[b] = st.sidebar.number_input(f"{b}", value=0.0)
else:
    st.sidebar.caption("(Tidak ada bahan pada AHSP ini)")

# ==============================
# HARGA ALAT
# ==============================
st.sidebar.subheader("Harga Alat (Rp)")
harga_alat = {}

if isinstance(row["alat_detail"], str) and row["alat_detail"] not in ["", "-"]:
    alat_list = [a.strip().rsplit(" ", 1)[0] for a in row["alat_detail"].split(";")]
    for a in alat_list:
        harga_alat[a] = st.sidebar.number_input(f"{a}", value=0.0)
else:
    st.sidebar.caption("(Tidak ada alat pada AHSP ini)")

# ==============================
# TAMBAH KE BOQ
# ==============================
if st.sidebar.button("Tambah ke BOQ"):
    hasil = sda_engine.hitung_rab(
        kode_ahsp=kode_terpilih,
        volume=volume,
        harga_tenaga=harga_tenaga,
        harga_bahan=harga_bahan,
        harga_alat=harga_alat,
    )
    st.session_state.boq.append(hasil)
    st.sidebar.success("Item berhasil ditambahkan")

# ==============================
# BOQ TABLE
# ==============================
st.subheader("BOQ – Daftar Pekerjaan")

if st.session_state.boq:
    boq_df = pd.DataFrame(st.session_state.boq)
    st.dataframe(boq_df[[
        "kode_ahsp",
        "uraian",
        "satuan",
        "volume",
        "biaya_tenaga",
        "biaya_bahan",
        "biaya_alat",
        "harga_satuan",
        "total",
    ]])

    # ==============================
    # REKAP
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
# DETAIL AHSP
# ==============================
st.subheader("Detail AHSP Reference")
st.json({
    "kode_ahsp": row["kode_ahsp"],
    "divisi": row["divisi"],
    "sub_divisi": row["sub_divisi"],
    "uraian": row["uraian_pekerjaan"],
    "metode": row["metode"],
    "satuan": row["satuan"],
    "tenaga_detail": row["tenaga_detail"],
    "bahan_detail": row["bahan_detail"],
    "alat_detail": row["alat_detail"],
    "sumber": row["sumber_ahsp"],
    "catatan": row["catatan"],
})

