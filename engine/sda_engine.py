"""
ENGINE RAB SDA – PHASE 1 (CORE)
Versi update:
- Tenaga + Bahan + Alat
- Database AHSP TIDAK diubah
- Audit-safe & deterministik
"""

import pandas as pd
from typing import Dict

AHSP_FILE = "data/ahsp_sda_2025_tanah_manual_core.xlsx"

# ==============================
# LOAD AHSP DATABASE
# ==============================
def load_ahsp(path: str = AHSP_FILE) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="ahsp_tanah_manual_core")

# ==============================
# PARSER UMUM (TENAGA / BAHAN / ALAT)
# ==============================
def parse_detail(detail: str) -> Dict[str, float]:
    """
    contoh:
    'Pekerja (L.01) 0.050; Mandor (L.04) 0.005'
    'Semen 50kg 0.12; Pasir 0.045'
    """
    result = {}
    if not isinstance(detail, str) or detail.strip() in ["", "-"]:
        return result

    parts = detail.split(";")
    for p in parts:
        p = p.strip()
        if not p:
            continue
        name, value = p.rsplit(" ", 1)
        result[name.strip()] = float(value)
    return result

# ==============================
# HITUNG BIAYA KOMPONEN
# ==============================
def hitung_biaya(detail: str, harga: Dict[str, float]) -> float:
    biaya = 0.0
    komponen = parse_detail(detail)
    for nama, koef in komponen.items():
        biaya += koef * harga.get(nama, 0)
    return biaya

# ==============================
# HITUNG HARGA SATUAN & TOTAL
# ==============================
def hitung_rab(
    kode_ahsp: str,
    volume: float,
    harga_tenaga: Dict[str, float],
    harga_bahan: Dict[str, float] = None,
    harga_alat: Dict[str, float] = None,
):
    harga_bahan = harga_bahan or {}
    harga_alat = harga_alat or {}

    df = load_ahsp()
    row = df[df["kode_ahsp"] == kode_ahsp]
    if row.empty:
        raise ValueError(f"AHSP {kode_ahsp} tidak ditemukan")

    row = row.iloc[0]

    biaya_tenaga = hitung_biaya(row["tenaga_detail"], harga_tenaga)
    biaya_bahan = hitung_biaya(row["bahan_detail"], harga_bahan)
    biaya_alat = hitung_biaya(row["alat_detail"], harga_alat)

    harga_satuan = biaya_tenaga + biaya_bahan + biaya_alat
    total = harga_satuan * volume

    return {
        "kode_ahsp": row["kode_ahsp"],
        "uraian": row["uraian_pekerjaan"],
        "satuan": row["satuan"],
        "volume": volume,
        "biaya_tenaga": biaya_tenaga,
        "biaya_bahan": biaya_bahan,
        "biaya_alat": biaya_alat,
        "harga_satuan": harga_satuan,
        "total": total,
    }
