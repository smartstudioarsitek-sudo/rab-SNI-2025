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
        
# Saran penambahan error handling pada engine
def hitung_rab(kode_ahsp, volume, harga_tenaga, koefisien_tenaga, uraian_pekerjaan, satuan):
    try:
        hsp_tenaga = 0.0
        for jenis_tenaga, harga_upah in harga_tenaga.items():
            # Menggunakan .get() dengan default 0 untuk mencegah KeyError
            koef = float(koefisien_tenaga.get(jenis_tenaga, 0.0))
            hsp_tenaga += koef * harga_upah
        
        total_harga = hsp_tenaga * volume
        
        return {
            "kode_ahsp": kode_ahsp,
            "uraian": uraian_pekerjaan,
            "satuan": satuan,
            "volume": volume,
            "hsp_tenaga": hsp_tenaga,
            "harga_satuan": hsp_tenaga, # Nanti ditambah bahan + alat
            "total": total_harga
        }
    except Exception as e:
        return {"error": str(e)}
    }

