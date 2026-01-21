def hitung_rab(
    kode_ahsp, 
    uraian_pekerjaan, 
    satuan, 
    volume, 
    harga_tenaga, koefisien_tenaga,
    harga_bahan, koefisien_bahan,
    harga_alat, koefisien_alat
):
    """
    Engine Deterministik - Menghitung RAB Lengkap (Tenaga + Bahan + Alat)
    """
    
    # --- 1. HITUNG SUB-TOTAL TENAGA ---
    hsp_tenaga = 0.0
    for nama, koef in koefisien_tenaga.items():
        harga = harga_tenaga.get(nama, 0)
        hsp_tenaga += koef * harga

    # --- 2. HITUNG SUB-TOTAL BAHAN ---
    hsp_bahan = 0.0
    for nama, koef in koefisien_bahan.items():
        harga = harga_bahan.get(nama, 0)
        hsp_bahan += koef * harga

    # --- 3. HITUNG SUB-TOTAL ALAT ---
    hsp_alat = 0.0
    for nama, koef in koefisien_alat.items():
        harga = harga_alat.get(nama, 0)
        hsp_alat += koef * harga

    # --- 4. REKAPITULASI ---
    hsp_total = hsp_tenaga + hsp_bahan + hsp_alat
    total_harga = volume * hsp_total

    return {
        "kode_ahsp": kode_ahsp,
        "uraian": uraian_pekerjaan,
        "satuan": satuan,
        "volume": volume,
        "hsp_tenaga": hsp_tenaga,
        "hsp_bahan": hsp_bahan,
        "hsp_alat": hsp_alat,
        "harga_satuan": hsp_total, # HSP Gabungan
        "total": total_harga
    }
