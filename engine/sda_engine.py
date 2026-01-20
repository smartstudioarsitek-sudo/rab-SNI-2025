# File: engine/sda_engine.py

def hitung_rab(kode_ahsp, volume, harga_tenaga, koefisien_tenaga, uraian_pekerjaan, satuan):
    """
    Menghitung RAB per item pekerjaan (Deterministik).
    
    Args:
        kode_ahsp (str): Kode item (contoh: T.01)
        volume (float): Volume pekerjaan
        harga_tenaga (dict): Dict harga satuan upah { 'Pekerja (L.01)': 100000, ... }
        koefisien_tenaga (dict): Dict koefisien { 'Pekerja (L.01)': 0.5, ... }
        uraian_pekerjaan (str): Nama pekerjaan
        satuan (str): Satuan (m3, m2, dll)
    
    Returns:
        dict: Summary perhitungan untuk tabel BOQ
    """
    
    # 1. Hitung Harga Satuan Pekerjaan (HSP)
    hsp_tenaga = 0.0
    
    # Loop setiap tenaga kerja (Pekerja, Mandor, dll)
    for jenis_tenaga, harga_upah in harga_tenaga.items():
        # Ambil koefisien jika ada, jika tidak 0
        koef = koefisien_tenaga.get(jenis_tenaga, 0.0)
        biaya = koef * harga_upah
        hsp_tenaga += biaya

    # Total Harga Satuan (HSP)
    # (Di sini baru tenaga, nanti bisa ditambah bahan/alat di Phase selanjutnya)
    harga_satuan_final = hsp_tenaga 

    # 2. Hitung Total Harga (Volume x Harga Satuan)
    total_harga = volume * harga_satuan_final

    # 3. Return Dictionary untuk ditampilkan di Tabel
    return {
        "kode_ahsp": kode_ahsp,
        "uraian": uraian_pekerjaan,
        "satuan": satuan,
        "volume": volume,
        "harga_satuan": harga_satuan_final,
        "total": total_harga
    }
