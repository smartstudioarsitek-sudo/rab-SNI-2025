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
import io
import xlsxwriter

# --- FUNGSI EKSPOR EXCEL (FORMAT STANDAR KONTRAKTOR) ---
def export_to_excel(df):
    output = io.BytesIO()
    # Inisialisasi workbook dengan engine xlsxwriter
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("RAB_SDA")

    # 1. Definisi Format
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    currency_format = workbook.add_format({
        'num_format': '#,##0', 'border': 1, 'valign': 'vcenter'
    })
    text_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
    center_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
    title_format = workbook.add_format({'bold': True, 'size': 14})

    # 2. Judul Laporan
    worksheet.write('A1', 'RENCANA ANGGARAN BIAYA (RAB)', title_format)
    worksheet.write('A2', 'Proyek: Analisis SDA Terintegrasi 2025', workbook.add_format({'bold': True}))
    
    # 3. Header Tabel
    headers = ['No', 'Kode AHSP', 'Uraian Pekerjaan', 'Satuan', 'Volume', 'Harga Satuan (Rp)', 'Total Harga (Rp)']
    for col_num, header in enumerate(headers):
        worksheet.write(4, col_num, header, header_format)

    # 4. Isi Data
    total_keseluruhan = 0
    for row_num, row in df.iterrows():
        r = row_num + 5
        worksheet.write(r, 0, row_num + 1, center_format)
        worksheet.write(r, 1, row['kode_ahsp'], text_format)
        worksheet.write(r, 2, row['uraian'], text_format)
        worksheet.write(r, 3, row['satuan'], center_format)
        worksheet.write(r, 4, row['volume'], text_format)
        worksheet.write(r, 5, row['harga_satuan'], currency_format)
        worksheet.write(r, 6, row['total'], currency_format)
        total_keseluruhan += row['total']

    # 5. Baris Total
    last_row = len(df) + 5
    worksheet.merge_range(last_row, 0, last_row, 5, 'TOTAL KESELURUHAN', header_format)
    worksheet.write(last_row, 6, total_keseluruhan, currency_format)

    # 6. Atur Lebar Kolom
    worksheet.set_column('A:A', 5)
    worksheet.set_column('B:B', 15)
    worksheet.set_column('C:C', 45)
    worksheet.set_column('D:D', 10)
    worksheet.set_column('E:G', 18)

    workbook.close()
    return output.getvalue()

# --- TOMBOL DOWNLOAD PADA UI ---
if "boq" in st.session_state and st.session_state.boq:
    # (Kode dataframe Anda yang sudah ada...)
    
    st.write("### 📥 Ekspor Dokumen")
    excel_data = export_to_excel(pd.DataFrame(st.session_state.boq))
    
    st.download_button(
        label="⬇️ Download RAB (Excel)",
        data=excel_data,
        file_name="RAB_JIAT_SmartStudio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def hitung_hsp_total(koefisien_data, harga_satuan_raya):
    """
    koefisien_data: list of dict berisi {tipe: 'bahan', nama: 'Semen', koef: 0.1}
    harga_satuan_raya: dict harga terbaru dari user
    """
    total_upah = 0
    total_bahan = 0
    total_alat = 0
    
    for item in koefisien_data:
        biaya = item['koef'] * harga_satuan_raya.get(item['nama'], 0)
        if item['tipe'] == 'tenaga': total_upah += biaya
        elif item['tipe'] == 'bahan': total_bahan += biaya
        elif item['tipe'] == 'alat': total_alat += biaya
        
    hsp_total = total_upah + total_bahan + total_alat
    return hsp_total, total_upah, total_bahan, total_alat
    }



