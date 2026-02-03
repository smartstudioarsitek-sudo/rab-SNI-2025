import pandas as pd
import io
import json # Import json for parsing potential JSON strings

def hitung_rab_lengkap(
    volume: float,
    koef_tenaga: dict,
    koef_bahan: dict,
    koef_alat: dict,
    harga_tenaga: dict,
    harga_bahan: dict,
    harga_alat: dict,
    persen_overhead: float = 15.0, # DEFAULT INI AKAN DITIMPA DARI UI
    persen_ppn: float = 11.0 # DEFAULT PPN 11%
):
    """
    Menghitung harga satuan pekerjaan dan total RAB untuk satu item pekerjaan.

    Args:
        volume (float): Volume pekerjaan (misal: m3, m2, ls).
        koef_tenaga (dict): Dictionary koefisien tenaga kerja. {'Pekerja': 0.5, 'Mandor': 0.05}
        koef_bahan (dict): Dictionary koefisien bahan. {'Semen PC': 100, 'Pasir': 0.5}
        koef_alat (dict): Dictionary koefisien alat. {'Excavator': 0.1, 'Alat Bantu': 0.01}
        harga_tenaga (dict): Dictionary harga satuan tenaga kerja. {'Pekerja': 100000}
        harga_bahan (dict): Dictionary harga satuan bahan. {'Semen PC': 1500}
        harga_alat (dict): Dictionary harga satuan alat. {'Excavator': 500000}
        persen_overhead (float): Persentase overhead dan profit (misal: 15.0 untuk 15%).
        persen_ppn (float): Persentase PPN (misal: 11.0 untuk 11%).

    Returns:
        dict: Dictionary berisi meta informasi dan detail biaya.
              Contoh: {"meta": {...}, "biaya": {...}}
    """
    total_biaya_tenaga = 0
    detail_biaya_tenaga = {}
    for nama, koef in koef_tenaga.items():
        harga_satuan = harga_tenaga.get(nama, 0)
        biaya = float(koef) * harga_satuan
        total_biaya_tenaga += biaya
        detail_biaya_tenaga[nama] = biaya

    total_biaya_bahan = 0
    detail_biaya_bahan = {}
    for nama, koef in koef_bahan.items():
        harga_satuan = harga_bahan.get(nama, 0)
        biaya = float(koef) * harga_satuan
        total_biaya_bahan += biaya
        detail_biaya_bahan[nama] = biaya

    total_biaya_alat = 0
    detail_biaya_alat = {}
    for nama, koef in koef_alat.items():
        harga_satuan = harga_alat.get(nama, 0)
        biaya = float(koef) * harga_satuan
        total_biaya_alat += biaya
        detail_biaya_alat[nama] = biaya

    jumlah_biaya_dasar = total_biaya_tenaga + total_biaya_bahan + total_biaya_alat
    nilai_overhead = jumlah_biaya_dasar * (persen_overhead / 100)
    hsp_tanpa_ppn = jumlah_biaya_dasar + nilai_overhead
    nilai_ppn = hsp_tanpa_ppn * (persen_ppn / 100)
    hsp_dengan_ppn = hsp_tanpa_ppn + nilai_ppn

    total_harga_tenaga_item = total_biaya_tenaga * volume
    total_harga_bahan_item = total_biaya_bahan * volume
    total_harga_alat_item = total_biaya_alat * volume
    total_sub_langsung_item = jumlah_biaya_dasar * volume # Biaya langsung per item
    total_overhead_item = nilai_overhead * volume
    total_hsp_tanpa_ppn_item = hsp_tanpa_ppn * volume
    total_ppn_item = nilai_ppn * volume
    total_hsp_dengan_ppn_item = hsp_dengan_ppn * volume

    return {
        "meta": {
            "volume": volume,
            "persen_overhead": persen_overhead,
            "persen_ppn": persen_ppn
        },
        "biaya": {
            "hsp_tenaga": total_biaya_tenaga,
            "hsp_bahan": total_biaya_bahan,
            "hsp_alat": total_biaya_alat,
            "hsp_sub_langsung": jumlah_biaya_dasar, # HSP biaya langsung
            "hsp_overhead": nilai_overhead,
            "hsp_tanpa_ppn": hsp_tanpa_ppn,
            "hsp_ppn": nilai_ppn,
            "hsp_dengan_ppn": hsp_dengan_ppn,

            "total_tenaga_item": total_harga_tenaga_item,
            "total_bahan_item": total_harga_bahan_item,
            "total_alat_item": total_harga_alat_item,
            "total_sub_langsung_item": total_sub_langsung_item, # Total biaya langsung per item
            "total_overhead_item": total_overhead_item,
            "total_tanpa_ppn_item": total_hsp_tanpa_ppn_item,
            "total_ppn_item": total_ppn_item,
            "total_dengan_ppn_item": total_hsp_dengan_ppn_item,
        },
        "detail_koef_harga": { # Tambahan untuk debugging atau detail lebih lanjut
            "tenaga": {"koef": koef_tenaga, "harga": harga_tenaga, "biaya_hsp": detail_biaya_tenaga},
            "bahan": {"koef": koef_bahan, "harga": harga_bahan, "biaya_hsp": detail_biaya_bahan},
            "alat": {"koef": koef_alat, "harga": harga_alat, "biaya_hsp": detail_biaya_alat},
        }
    }

def export_to_excel(df_rab: pd.DataFrame, nama_proyek="RAB Proyek"):
    """
    Mengekspor DataFrame RAB ke format Excel dengan formatting profesional.

    Args:
        df_rab (pd.DataFrame): DataFrame yang berisi data RAB.
        nama_proyek (str): Nama proyek untuk judul laporan.

    Returns:
        bytes: Isi file Excel dalam format bytes.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = writer.sheets['RAB Project']

        # Define formats
        fmt_header = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#DDEBF7'})
        fmt_currency = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        fmt_currency_bold = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'bold': True, 'border': 1, 'bg_color': '#FFF2CC'})
        fmt_text = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1})
        fmt_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center'})
        fmt_total_label = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#DDEBF7', 'border': 1})
        fmt_total_value = workbook.add_format({'num_format': '#,##0.00', 'bold': True, 'align': 'right', 'bg_color': '#DDEBF7', 'border': 1})

        # Write title
        worksheet.merge_range('A1:P1', 'LAPORAN RENCANA ANGGARAN BIAYA', fmt_title)
        worksheet.merge_range('A2:P2', f'PROYEK: {nama_proyek.upper()}', fmt_subtitle)
        worksheet.merge_range('A3:P3', f'Sumber Data: SNI 2025 by The Gems Grandmaster', workbook.add_format({'align': 'center', 'italic': True}))
        worksheet.write_blank('A4:P4', None, workbook.add_format({'top': 1, 'bottom': 1})) # Line separator

        start_row = 5 # Start writing headers from row 5

        # Define columns and their widths
        columns = [
            {'header': 'No.', 'width': 5, 'format': fmt_center},
            {'header': 'Uraian Pekerjaan', 'width': 40, 'format': fmt_text},
            {'header': 'Satuan', 'width': 10, 'format': fmt_center},
            {'header': 'Volume', 'width': 12, 'format': fmt_currency},
            {'header': 'HSP (Rp) Tenaga', 'width': 15, 'format': fmt_currency},
            {'header': 'HSP (Rp) Bahan', 'width': 15, 'format': fmt_currency},
            {'header': 'HSP (Rp) Alat', 'width': 15, 'format': fmt_currency},
            {'header': 'HSP (Rp) Sub Total Langsung', 'width': 20, 'format': fmt_currency}, # New detail
            {'header': 'HSP (Rp) Overhead & Profit', 'width': 20, 'format': fmt_currency}, # New detail
            {'header': 'HSP (Rp) Tanpa PPN', 'width': 20, 'format': fmt_currency_bold}, # New detail
            {'header': 'Total Biaya (Rp) Tenaga', 'width': 20, 'format': fmt_currency},
            {'header': 'Total Biaya (Rp) Bahan', 'width': 20, 'format': fmt_currency},
            {'header': 'Total Biaya (Rp) Alat', 'width': 20, 'format': fmt_currency},
            {'header': 'Total Biaya (Rp) Sub Total Langsung', 'width': 25, 'format': fmt_currency}, # New detail
            {'header': 'Total Biaya (Rp) Overhead & Profit', 'width': 25, 'format': fmt_currency}, # New detail
            {'header': 'Total Biaya (Rp) Tanpa PPN', 'width': 25, 'format': fmt_currency_bold},
        ]

        # Write headers
        for col_num, col_data in enumerate(columns):
            worksheet.write(start_row, col_num, col_data['header'], fmt_header)
            worksheet.set_column(col_num, col_num, col_data['width'])

        # Write data rows
        for row_num, (index, row_data) in enumerate(df_rab.iterrows(), start=start_row + 1):
            worksheet.write(row_num, 0, row_num - start_row, fmt_center) # No
            worksheet.write(row_num, 1, row_data['Uraian Pekerjaan'], fmt_text)
            worksheet.write(row_num, 2, row_data['Satuan'], fmt_center)
            worksheet.write(row_num, 3, row_data['Volume'], fmt_currency)
            worksheet.write(row_num, 4, row_data['HSP Tenaga'], fmt_currency)
            worksheet.write(row_num, 5, row_data['HSP Bahan'], fmt_currency)
            worksheet.write(row_num, 6, row_data['HSP Alat'], fmt_currency)
            worksheet.write(row_num, 7, row_data['HSP Sub Total Langsung'], fmt_currency)
            worksheet.write(row_num, 8, row_data['HSP OHP'], fmt_currency)
            worksheet.write(row_num, 9, row_data['HSP Tanpa PPN'], fmt_currency_bold)
            worksheet.write(row_num, 10, row_data['Total Tenaga'], fmt_currency)
            worksheet.write(row_num, 11, row_data['Total Bahan'], fmt_currency)
            worksheet.write(row_num, 12, row_data['Total Alat'], fmt_currency)
            worksheet.write(row_num, 13, row_data['Total Sub Total Langsung'], fmt_currency)
            worksheet.write(row_num, 14, row_data['Total OHP'], fmt_currency)
            worksheet.write(row_num, 15, row_data['Total Tanpa PPN'], fmt_currency_bold)


        # Add summary totals
        total_rows = len(df_rab)
        current_row = start_row + 1 + total_rows

        # Calculate totals
        grand_total_sub_langsung = df_rab['Total Sub Total Langsung'].sum()
        grand_total_ohp = df_rab['Total OHP'].sum()
        grand_total_tanpa_ppn = df_rab['Total Tanpa PPN'].sum()
        grand_total_ppn = grand_total_tanpa_ppn * (df_rab['PPN (%)'].iloc[0] / 100) if not df_rab.empty else 0 # Ambil PPN dari baris pertama
        grand_total_dengan_ppn = grand_total_tanpa_ppn + grand_total_ppn

        # Write summary labels
        worksheet.merge_range(current_row, 0, current_row, 12, 'TOTAL BIAYA LANGSUNG', fmt_total_label)
        worksheet.write(current_row, 13, grand_total_sub_langsung, fmt_total_value)
        worksheet.merge_range(current_row, 14, current_row, 15, '', fmt_total_value) # Merge untuk align total

        current_row += 1
        worksheet.merge_range(current_row, 0, current_row, 12, 'TOTAL OVERHEAD & PROFIT', fmt_total_label)
        worksheet.write(current_row, 13, grand_total_ohp, fmt_total_value)
        worksheet.merge_range(current_row, 14, current_row, 15, '', fmt_total_value)

        current_row += 1
        worksheet.merge_range(current_row, 0, current_row, 12, 'GRAND TOTAL (TANPA PPN)', fmt_total_label)
        worksheet.write(current_row, 13, grand_total_tanpa_ppn, fmt_total_value)
        worksheet.merge_range(current_row, 14, current_row, 15, '', fmt_total_value)

        current_row += 1
        worksheet.merge_range(current_row, 0, current_row, 12, f'PPN ({df_rab["PPN (%)"].iloc[0] if not df_rab.empty else 0}%)', fmt_total_label)
        worksheet.write(current_row, 13, grand_total_ppn, fmt_total_value)
        worksheet.merge_range(current_row, 14, current_row, 15, '', fmt_total_value)

        current_row += 1
        worksheet.merge_range(current_row, 0, current_row, 12, 'GRAND TOTAL (DENGAN PPN)', fmt_total_label)
        worksheet.write(current_row, 13, grand_total_dengan_ppn, fmt_total_value)
        worksheet.merge_range(current_row, 14, current_row, 15, '', fmt_total_value)

    output.seek(0)
    return output.getvalue()
