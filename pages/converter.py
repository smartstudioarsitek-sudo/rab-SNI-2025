import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Mesin Konversi AHSP V3", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP (V3 - Smart Detect)")
st.caption("Support: Excel Multi-Sheet, Kolom Geser, & Format Data_RAB")

# ==========================================
# 1. CORE ENGINE (LOGIKA CERDAS)
# ==========================================

def is_number(s):
    """Cek apakah string adalah angka"""
    try:
        float(str(s).replace(',', '').replace(' ', ''))
        return True
    except:
        return False

def clean_decimal(s):
    """Membersihkan format angka (1.000,00 jadi 1000.00 atau 0,05 jadi 0.05)"""
    s = str(s).strip()
    # Kasus 1.000,00 (Indo) -> 1000.00
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    # Kasus 0,05 (Indo) -> 0.05
    elif ',' in s:
        s = s.replace(',', '.')
    return float(s)

def parse_smart_excel(df_sheet):
    """
    Membaca DataFrame Excel dan mencari pola AHSP secara dinamis.
    Tidak peduli kolom ke berapa, yang penting urutannya logis.
    """
    data_list = []
    
    # State
    current_data = {'kode': '', 'uraian': '', 'satuan': 'ls', 'tenaga': [], 'bahan': [], 'alat': []}
    mode = None # tenaga / bahan / alat
    
    # Ubah DF jadi list of list biar gampang di-loop
    # Isi Na dengan string kosong
    rows = df_sheet.fillna("").values.tolist()
    
    for row in rows:
        # Bersihkan spasi di setiap sel
        row = [str(cell).strip() for cell in row]
        
        # Gabungkan semua teks di baris ini untuk deteksi kata kunci
        full_text_row = " ".join(row).upper()
        
        # --- 1. DETEKSI MODE (JUDUL KATEGORI) ---
        if "TENAGA" in full_text_row and "JUMLAH" not in full_text_row: mode = 'tenaga'; continue
        if "BAHAN" in full_text_row and "JUMLAH" not in full_text_row: mode = 'bahan'; continue
        if ("ALAT" in full_text_row or "PERALATAN" in full_text_row) and "JUMLAH" not in full_text_row: mode = 'alat'; continue
        
        # --- 2. DETEKSI KODE & URAIAN PEKERJAAN (HEADER) ---
        # Cari sel yang isinya pola kode (misal: 2.2.1.1)
        # Dan sel di sebelahnya ada teks panjang
        found_code = False
        for i, cell in enumerate(row):
            # Regex kode: Angka.Angka (Minimal 2 segmen, misal 2.1 atau A.2.1)
            if re.match(r'^[A-Z0-9]+\.[\d\.]+$', cell) and len(cell) < 15:
                # Cek sebelah kanannya apakah ada Uraian?
                # Cari sel non-kosong berikutnya
                uraian_text = ""
                satuan_text = "ls" # Default
                
                for j in range(i+1, len(row)):
                    if row[j]: 
                        uraian_text = row[j]
                        # Coba cari satuan di sel berikutnya lagi
                        for k in range(j+1, len(row)):
                            if row[k] and len(row[k]) < 10: # Asumsi satuan pendek
                                satuan_text = row[k]
                                break
                        break
                
                if uraian_text and "ANALISA" not in uraian_text.upper():
                    # SIMPAN DATA SEBELUMNYA
                    if current_data['kode']:
                        data_list.append(export_item(current_data))
                    
                    # RESET BARU
                    current_data = {
                        'kode': cell, 'uraian': uraian_text, 'satuan': satuan_text,
                        'tenaga': [], 'bahan': [], 'alat': []
                    }
                    mode = None # Reset mode kalau ganti pekerjaan
                    found_code = True
                    break
        
        if found_code: continue

        # --- 3. DETEKSI KOEFISIEN (ISI RESEP) ---
        if mode and current_data['kode']:
            # Cari baris yang punya format: [Nama Item] ... [Angka Koefisien]
            # Strategi: Cari sel teks (Nama) dan sel Angka (Koefisien)
            
            nama_item = ""
            koefisien = ""
            
            # 1. Cari Nama Item (String panjang, bukan angka, bukan 'OH', bukan 'M3')
            # Biasanya di kolom awal-awal yang ada isinya
            col_idx_nama = -1
            for i, cell in enumerate(row):
                if cell and not is_number(cell) and len(cell) > 2 and cell.lower() not in ['oh', 'ls', 'bh', 'set', 'unit']:
                    # Hindari kata-kata sampah
                    if any(x in cell.upper() for x in ['NO', 'URAIAN', 'SAT', 'KOEF', 'JUMLAH']): continue
                    nama_item = cell
                    col_idx_nama = i
                    break
            
            # 2. Cari Koefisien (Angka) SETELAH Nama Item
            if nama_item and col_idx_nama != -1:
                for j in range(col_idx_nama + 1, len(row)):
                    cell = row[j]
                    # Cek apakah angka valid
                    if cell and is_number(cell):
                        val = clean_decimal(cell)
                        # Koefisien biasanya < 1000. Kalau > 1000 biasanya Harga.
                        # Tapi semen beton bisa 300kg. Jadi kita ambil angka pertama yang ketemu setelah nama.
                        if val > 0:
                            koefisien = val
                            break
            
            # 3. Simpan jika valid
            if nama_item and koefisien:
                entry = f"{nama_item} {koefisien}"
                current_data[mode].append(entry)

    # Simpan item terakhir
    if current_data['kode']:
        data_list.append(export_item(current_data))
        
    return data_list

def export_item(d):
    return {
        'kode': d['kode'], 'uraian': d['uraian'], 'satuan': d['satuan'],
        'tenaga': ";".join(d['tenaga']) if d['tenaga'] else "-",
        'bahan': ";".join(d['bahan']) if d['bahan'] else "-",
        'alat': ";".join(d['alat']) if d['alat'] else "-"
    }

# ==========================================
# 2. UI UTAMA
# ==========================================

uploaded_file = st.file_uploader("Upload File `data_rab.xlsx`", type=['xlsx', 'csv'])

if uploaded_file:
    with st.spinner("🚀 Sedang memproses file 'Raksasa'... (Mohon bersabar)"):
        try:
            all_data = []
            
            if uploaded_file.name.endswith('.xlsx'):
                xls = pd.ExcelFile(uploaded_file)
                total_sheets = len(xls.sheet_names)
                my_bar = st.progress(0)
                
                for i, sheet_name in enumerate(xls.sheet_names):
                    # Update progress
                    my_bar.progress((i + 1) / total_sheets)
                    
                    # Baca sheet (header=None biar kolom kosong terbaca)
                    df_sheet = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    
                    # Parse Sheet Ini
                    sheet_results = parse_smart_excel(df_sheet)
                    all_data.extend(sheet_results)
                    
            else:
                # Kalau CSV
                df = pd.read_csv(uploaded_file, header=None, sep=None, engine='python')
                all_data = parse_smart_excel(df)

            # Hasil Akhir
            df_hasil = pd.DataFrame(all_data)
            
            if not df_hasil.empty:
                st.success(f"✅ SUKSES BESAR! Berhasil menarik **{len(df_hasil)}** Analisa Pekerjaan!")
                
                with st.expander("🔍 Intip Hasil Data"):
                    st.dataframe(df_hasil.head(50))
                
                # Download Button
                csv_export = df_hasil.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download ahsp_ciptakarya_master.csv",
                    data=csv_export,
                    file_name="ahsp_ciptakarya_master.csv",
                    mime="text/csv",
                    type="primary"
                )
                st.info("Langkah Selanjutnya: Upload file ini ke GitHub folder `data/`.")
            else:
                st.error("❌ Data tidak ditemukan. Coba cek format file Excelnya.")
                
        except Exception as e:
            st.error(f"Error: {e}")
