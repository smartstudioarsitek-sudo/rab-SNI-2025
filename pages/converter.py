import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Mesin Konversi V4 (Final)", page_icon="🏭")
st.title("🏭 Mesin Pencetak AHSP (V4 - Filter Cerdas)")
st.info("Versi ini otomatis membuang data sampah (Rekap/BBS) dan hanya mengambil Analisa Murni.")

# ==========================================
# 1. CORE LOGIC (FILTER CERDAS)
# ==========================================

def clean_decimal(s):
    """Membersihkan format angka Indonesia (koma -> titik)"""
    s = str(s).strip()
    if ',' in s and '.' not in s: # 0,05 -> 0.05
        s = s.replace(',', '.')
    return pd.to_numeric(s, errors='coerce')

def parse_excel_smart(df_sheet):
    """
    Logika Detektif: Hanya mengambil blok yang terlihat seperti Analisa AHSP.
    Mengabaikan Rekap, BBS, dan Daftar Harga.
    """
    data_list = []
    
    # State
    current_item = {}
    mode = None # tenaga / bahan / alat
    
    # Konversi ke list of strings biar cepat
    rows = df_sheet.fillna("").astype(str).values.tolist()
    
    for row in rows:
        # Bersihkan spasi
        row = [cell.strip() for cell in row]
        row_text = " ".join(row).upper()
        
        # --- A. DETEKSI JUDUL PEKERJAAN (HEADER) ---
        # Ciri: Ada Kode (angka.angka) DAN Uraian Panjang DAN TIDAK ADA kata "Total"
        found_header = False
        if not mode: # Hanya cari header kalau sedang tidak baca rincian
            for i, cell in enumerate(row):
                # Regex Kode: Minimal 2 segmen angka (misal 2.2.1) dan panjang < 15
                if re.match(r'^[A-Z0-9]+\.[\d\.]+$', cell) and len(cell) < 15:
                    
                    # Cek Uraian di sebelah kanan
                    uraian = ""
                    satuan = "ls"
                    
                    for j in range(i+1, min(i+5, len(row))):
                        if len(row[j]) > 5 and not re.match(r'^[\d\.,]+$', row[j]): # Teks panjang bukan angka
                            uraian = row[j]
                            # Cek satuan di kanannya lagi
                            if j+1 < len(row):
                                s_cal = row[j+1].lower()
                                if len(s_cal) < 10 and s_cal in ['m', "m'", 'm2', 'm3', 'bh', 'buah', 'ls', 'unit', 'kg', 'set']:
                                    satuan = s_cal
                            break
                    
                    # Validasi Header: Bukan baris rekap
                    if uraian and "JUMLAH" not in uraian.upper() and "TOTAL" not in uraian.upper():
                        # Simpan data sebelumnya
                        if current_item:
                            data_list.append(export_item(current_item))
                        
                        # Reset item baru
                        current_item = {
                            'kode': cell, 'uraian': uraian, 'satuan': satuan,
                            'tenaga': [], 'bahan': [], 'alat': []
                        }
                        found_header = True
                        break
        
        if found_header: continue

        # --- B. DETEKSI KATEGORI (TENAGA/BAHAN/ALAT) ---
        if not current_item: continue # Jangan cari mode kalau belum ketemu judul pekerjaan
        
        if "TENAGA" in row_text and "JUMLAH" not in row_text: mode = 'tenaga'; continue
        if "BAHAN" in row_text and "JUMLAH" not in row_text: mode = 'bahan'; continue
        if ("ALAT" in row_text or "PERALATAN" in row_text) and "JUMLAH" not in row_text: mode = 'alat'; continue
        
        # --- C. AMBIL ISI (KOEFISIEN) ---
        if mode:
            # Cari baris yang punya format: [Nama Item] ... [Angka Koefisien]
            # Syarat Nama: Teks panjang, bukan 'OH', bukan 'M3'
            # Syarat Koefisien: Angka desimal < 1000 (biasanya)
            
            nama_res = ""
            koef_res = 0.0
            
            for i, cell in enumerate(row):
                # Deteksi Nama Sumber Daya
                if len(cell) > 2 and not re.match(r'^[\d\.,]+$', cell): # Teks bukan angka
                    if cell.lower() in ['oh', 'orang', 'ls', 'bh', 'set', 'unit', 'sewa', 'jam']: continue
                    if "JUMLAH" in cell.upper() or "TOTAL" in cell.upper() or "HARGA" in cell.upper(): break # Stop baris ini
                    
                    nama_res = cell
                    
                    # Cari Koefisien (Angka pertama valid di sebelah kanan nama)
                    for k in range(i+1, len(row)):
                        val = clean_decimal(row[k])
                        if pd.notna(val) and val > 0:
                            # Validasi tambahan: Koefisien jarang > 10000 (kecuali paku/kawat)
                            # Harga biasanya > 1000.
                            # Jadi kalau ketemu angka, kita anggap koefisien dulu.
                            koef_res = val
                            break
                    break
            
            if nama_res and koef_res > 0:
                # Format: "Semen 1.2"
                entry = f"{nama_res} {koef_res}"
                current_item[mode].append(entry)

    # Simpan item terakhir
    if current_item:
        data_list.append(export_item(current_item))
        
    return data_list

def export_item(d):
    # Gabungkan list menjadi string satu baris
    return {
        'kode': d['kode'],
        'uraian': d['uraian'],
        'satuan': d['satuan'],
        'tenaga': ";".join(d['tenaga']) if d['tenaga'] else "-",
        'bahan': ";".join(d['bahan']) if d['bahan'] else "-",
        'alat': ";".join(d['alat']) if d['alat'] else "-"
    }

# ==========================================
# 2. UI & EKSEKUSI
# ==========================================

uploaded_file = st.file_uploader("Upload `data_rab.xlsx`", type=['xlsx'])

if uploaded_file:
    with st.spinner("Sedang menyaring data (Membuang sampah Rekap & BBS)..."):
        try:
            xls = pd.ExcelFile(uploaded_file)
            all_analisa = []
            
            total_sheets = len(xls.sheet_names)
            prog_bar = st.progress(0)
            
            # Daftar sheet yang pasti SAMPAH (Boleh di-skip biar cepat)
            skip_keywords = ['REKAP', 'DAFTAR', 'HARGA', 'UPAH', 'BBS', 'TUKANG', 'VOLUME']
            
            for idx, sheet in enumerate(xls.sheet_names):
                prog_bar.progress((idx + 1) / total_sheets)
                
                # Skip sheet yang jelas-jelas bukan analisa
                if any(k in sheet.upper() for k in skip_keywords):
                    continue
                
                # Baca sheet
                df_sheet = pd.read_excel(xls, sheet_name=sheet, header=None)
                
                # Proses
                hasil_sheet = parse_excel_smart(df_sheet)
                all_analisa.extend(hasil_sheet)
                
            # Final DataFrame
            df_final = pd.DataFrame(all_analisa)
            
            # Pembersihan Akhir: Buang yang uraiannya aneh/kosong
            df_final = df_final[df_final['uraian'].str.len() > 3]
            
            st.success(f"✅ Selesai! Berhasil mengambil **{len(df_final)}** Analisa Bersih.")
            
            # Preview
            with st.expander("👁️ Cek Hasil (Pastikan Kolom Uraian Benar)"):
                st.dataframe(df_final)
            
            # Download
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download `ahsp_ciptakarya_master.csv`",
                csv,
                "ahsp_ciptakarya_master.csv",
                "text/csv",
                type="primary"
            )
            
        except Exception as e:
            st.error(f"Error: {e}")
