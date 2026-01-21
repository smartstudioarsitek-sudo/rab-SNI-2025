import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Mesin Konversi V5 (Final)", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP (V5 - Strict Mode)")
st.info("💡 Tips: Sebaiknya upload file Excel yang HANYA berisi sheet Analisa. Hapus sheet Rekap/BBS sebelum upload supaya hasil bersih.")

# ==========================================
# 1. CORE LOGIC (PENCARI KOEFISIEN)
# ==========================================

def clean_number(value):
    """Membersihkan angka dari string (misal: 'Rp 15.000' -> 15000.0)"""
    try:
        if pd.isna(value): return 0.0
        s = str(value).replace('Rp', '').replace(' ', '')
        
        # Cek format 1.000,00 (Indo) vs 1000.00 (US)
        if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.') # Indo -> US
        elif ',' in s: s = s.replace(',', '.') # Koma desimal -> Titik
        
        return float(s)
    except:
        return 0.0

def process_sheet_strict(df):
    """
    Hanya mengambil data jika menemukan pola tabel AHSP yang valid:
    [Kode] [Uraian] ... [Koefisien]
    """
    data_list = []
    
    # 1. CARI LOKASI KOLOM KOEFISIEN
    # Kita cari baris yang mengandung kata "KOEFISIEN" di header
    start_row = 0
    col_koef = -1
    col_uraian = -1
    col_kode = 0 # Default kolom pertama
    
    # Scan 20 baris pertama untuk cari header
    for r in range(min(20, len(df))):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "KOEFISIEN" in row_vals or "KOEF" in row_vals:
            start_row = r + 1
            # Cari index kolom
            for c, val in enumerate(row_vals):
                if "KOEF" in val: col_koef = c
                if "URAIAN" in val: col_uraian = c
            break
    
    if col_koef == -1:
        return [] # Skip sheet ini karena tidak ada tabel analisa

    # Jika kolom uraian tidak ketemu header-nya, asumsi di kolom ke-1
    if col_uraian == -1: col_uraian = 1

    # 2. SCAN DATA KE BAWAH
    current_item = {}
    mode = None # Tenaga/Bahan/Alat
    
    for r in range(start_row, len(df)):
        row = df.iloc[r].tolist()
        
        # Ambil nilai sel penting
        val_kode = str(row[col_kode]).strip() if len(row) > col_kode else ""
        val_uraian = str(row[col_uraian]).strip() if len(row) > col_uraian else ""
        val_koef = row[col_koef] if len(row) > col_koef else 0
        
        # --- A. DETEKSI JUDUL PEKERJAAN BARU ---
        # Ciri: Ada Kode (angka.angka) DAN Uraian panjang
        if re.match(r'^[A-Z0-9]+\.[\d\.]+$', val_kode) and len(val_kode) < 20:
            # Validasi tambahan: Uraian harus panjang (bukan cuma "Beton")
            if len(val_uraian) > 5:
                # Simpan yang lama
                if current_item: data_list.append(export_item(current_item))
                
                # Reset baru
                current_item = {
                    'kode': val_kode, 'uraian': val_uraian, 'satuan': 'ls',
                    'tenaga': [], 'bahan': [], 'alat': []
                }
                
                # Coba cari satuan di kolom-kolom sebelah uraian
                for c in range(col_uraian+1, len(row)):
                    s = str(row[c]).lower().strip()
                    if s in ['m', "m'", 'm2', 'm3', 'bh', 'buah', 'unit', 'kg', 'set', 'ls']:
                        current_item['satuan'] = s
                        break
                
                mode = None
                continue

        # --- B. DETEKSI KATEGORI ---
        txt_row = " ".join([str(x) for x in row]).upper()
        if "TENAGA" in txt_row and "JUMLAH" not in txt_row: mode = 'tenaga'; continue
        if "BAHAN" in txt_row and "JUMLAH" not in txt_row: mode = 'bahan'; continue
        if ("ALAT" in txt_row or "PERALATAN" in txt_row) and "JUMLAH" not in txt_row: mode = 'alat'; continue
        
        # --- C. AMBIL ISI (RESEP) ---
        if mode and current_item:
            # Syarat: Ada Uraian DAN Ada Angka Koefisien Valid (> 0)
            koef_float = clean_number(val_koef)
            
            if len(val_uraian) > 2 and koef_float > 0:
                # Hindari baris sampah (Total, Jumlah, Overhead)
                if any(x in val_uraian.upper() for x in ['JUMLAH', 'TOTAL', 'BIAYA', 'OVERHEAD', 'PROFIT']):
                    continue
                
                # Masukkan ke resep
                entry = f"{val_uraian} {koef_float}"
                current_item[mode].append(entry)

    # Simpan sisa terakhir
    if current_item: data_list.append(export_item(current_item))
    return data_list

def export_item(d):
    return {
        'kode': d['kode'],
        'uraian': d['uraian'],
        'satuan': d['satuan'],
        'tenaga': ";".join(d['tenaga']) if d['tenaga'] else "-",
        'bahan': ";".join(d['bahan']) if d['bahan'] else "-",
        'alat': ";".join(d['alat']) if d['alat'] else "-"
    }

# ==========================================
# 2. UI UTAMA
# ==========================================

uploaded_file = st.file_uploader("Upload Excel Analisa (Wajib ada kolom Koefisien)", type=['xlsx'])

if uploaded_file:
    with st.spinner("Sedang memproses..."):
        try:
            xls = pd.ExcelFile(uploaded_file)
            all_data = []
            
            # Progress bar
            bar = st.progress(0)
            sheets = xls.sheet_names
            
            for i, sheet in enumerate(sheets):
                bar.progress((i+1)/len(sheets))
                
                # Skip sheet sampah (Opsional, filter manual lebih baik)
                if any(x in sheet.upper() for x in ['REKAP', 'DAFTAR', 'BBS', 'VOLUME']):
                    continue
                
                # Baca Sheet
                df = pd.read_excel(xls, sheet_name=sheet, header=None)
                
                # Proses
                res = process_sheet_strict(df)
                if res:
                    all_data.extend(res)
            
            if all_data:
                df_final = pd.DataFrame(all_data)
                st.success(f"✅ Berhasil mengambil **{len(df_final)}** Item Analisa!")
                
                # Preview
                st.dataframe(df_final.head())
                
                # Download
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "⬇️ Download Database Bersih",
                    csv,
                    "ahsp_ciptakarya_master.csv",
                    "text/csv",
                    type="primary"
                )
            else:
                st.error("❌ Tidak ditemukan data Analisa yang valid.")
                st.warning("Pastikan Excel Kakak punya kolom dengan judul 'Koefisien' di dalam tabel analisanya.")
                
        except Exception as e:
            st.error(f"Error: {e}")
