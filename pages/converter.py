import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Mesin Konversi V6 (Massal)", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP (V6 - Mass Upload)")
st.info("Tip: Blok semua file CSV/Excel yang sudah dipisah, lalu tarik ke sini sekaligus.")

# ==========================================
# 1. CORE LOGIC (SCANNER BARIS)
# ==========================================

def clean_decimal(s):
    """Membersihkan format angka 1.000,00 menjadi 1000.0"""
    s = str(s).strip()
    # Hapus Rp dan spasi
    s = s.replace('Rp', '').replace(' ', '')
    
    # Cek format desimal Indonesia (koma) vs US (titik)
    if ',' in s and '.' in s: 
        s = s.replace('.', '').replace(',', '.') # 1.000,00 -> 1000.00
    elif ',' in s: 
        s = s.replace(',', '.') # 0,05 -> 0.05
        
    try:
        return float(s)
    except:
        return 0.0

def parse_content(df_raw, source_filename):
    """
    Membaca DataFrame mentah dan mencari pola Analisa AHSP.
    Mengabaikan header tebal di atas.
    """
    data_list = []
    
    # Konversi ke List of Lists (String) biar mudah diproses
    rows = df_raw.fillna("").astype(str).values.tolist()
    
    current_item = {}
    mode = None # tenaga / bahan / alat
    
    for row in rows:
        # Bersihkan spasi di setiap sel
        row = [cell.strip() for cell in row]
        row_text = " ".join(row).upper()
        
        # --- 1. DETEKSI JUDUL PEKERJAAN (HEADER ANALISA) ---
        # Pola: Ada Kode (Angka.Angka) di kolom awal, dan Uraian panjang di kanannya
        found_header = False
        
        # Cek kolom 0 sampai 5 (siapa tau kolomnya geser)
        for i in range(min(5, len(row))):
            cell = row[i]
            # Regex: Minimal 2 segmen angka (misal 2.2.1 atau 6.4.1)
            # Dan panjang kode tidak boleh terlalu panjang (bukan kalimat)
            if re.match(r'^[A-Z0-9]+\.[\d\.]+$', cell) and len(cell) < 15:
                
                # Cek sebelah kanannya ada Uraian?
                uraian = ""
                satuan = "ls"
                
                # Cari teks panjang di sebelah kanan kode
                for j in range(i+1, min(i+5, len(row))):
                    if len(row[j]) > 5 and not re.match(r'^[\d\.,]+$', row[j]): # Teks, bukan angka
                        uraian = row[j]
                        
                        # Cek satuan di kanannya lagi
                        if j+1 < len(row):
                            val_sat = row[j+1].lower()
                            if val_sat in ['m', "m'", 'm2', 'm3', 'bh', 'buah', 'unit', 'kg', 'set', 'ls', 'titik']:
                                satuan = val_sat
                        break
                
                # Validasi: Uraian valid (bukan judul kolom)
                if uraian and "ANALISA" not in uraian.upper() and "JUMLAH" not in uraian.upper():
                    # Simpan data lama
                    if current_item: data_list.append(export_item(current_item))
                    
                    # Buat item baru
                    current_item = {
                        'kode': cell, 'uraian': uraian, 'satuan': satuan,
                        'tenaga': [], 'bahan': [], 'alat': []
                    }
                    mode = None # Reset mode
                    found_header = True
                    break
        
        if found_header: continue

        # --- 2. DETEKSI KATEGORI (TENAGA/BAHAN/ALAT) ---
        if not current_item: continue # Jangan baca kalau belum ketemu judul pekerjaan
        
        if "TENAGA" in row_text and "JUMLAH" not in row_text: mode = 'tenaga'; continue
        if "BAHAN" in row_text and "JUMLAH" not in row_text: mode = 'bahan'; continue
        if ("ALAT" in row_text or "PERALATAN" in row_text) and "JUMLAH" not in row_text: mode = 'alat'; continue
        
        # --- 3. AMBIL ISI KOEFISIEN ---
        if mode:
            # Cari pola: [Nama Item] ... [Angka Koefisien]
            nama_res = ""
            koef_res = 0.0
            
            for i, cell in enumerate(row):
                # Nama Item: Teks panjang, bukan angka, bukan satuan
                if len(cell) > 2 and not re.match(r'^[\d\.,]+$', cell): 
                    if cell.lower() in ['oh', 'orang', 'ls', 'bh', 'set', 'unit', 'sewa', 'jam', 'm3', 'kg']: continue
                    if any(x in cell.upper() for x in ['JUMLAH', 'TOTAL', 'HARGA', 'BIAYA']): break # Stop baris ini
                    
                    nama_res = cell
                    
                    # Cari Koefisien (Angka pertama valid di sebelah kanan nama)
                    for k in range(i+1, len(row)):
                        val_str = row[k]
                        # Koefisien biasanya < 1000. Kalau jutaan itu harga.
                        # Kecuali Paku/Kawat (bisa 50 gram -> 0.05 atau 50)
                        # Kita ambil angka pertama yang valid.
                        if re.match(r'^[\d\.,]+$', val_str):
                            val_float = clean_decimal(val_str)
                            if val_float > 0:
                                koef_res = val_float
                                break
                    break
            
            if nama_res and koef_res > 0:
                entry = f"{nama_res} {koef_res}"
                current_item[mode].append(entry)

    # Simpan item terakhir
    if current_item:
        data_list.append(export_item(current_item))
        
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
# 2. UI MASS UPLOAD
# ==========================================

# Izinkan upload banyak file sekaligus
uploaded_files = st.file_uploader(
    "Upload File CSV/Excel (Bisa banyak sekaligus!)", 
    type=['csv', 'xlsx'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🚀 Mulai Proses Semua File"):
        all_master_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(uploaded_files)
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Sedang memproses: {file.name}...")
            progress_bar.progress((i + 1) / total_files)
            
            try:
                # BACA FILE
                if file.name.endswith('.csv'):
                    # Gunakan engine python biar fleksibel sama delimiter
                    df = pd.read_csv(file, header=None, sep=None, engine='python')
                else:
                    df = pd.read_excel(file, header=None)
                
                # PARSING
                result = parse_content(df, file.name)
                
                if result:
                    all_master_data.extend(result)
                    
            except Exception as e:
                st.warning(f"Gagal membaca file {file.name}: {e}")
        
        # --- HASIL AKHIR ---
        if all_master_data:
            df_final = pd.DataFrame(all_master_data)
            
            # Buang duplikat kode (kalau ada)
            df_final = df_final.drop_duplicates(subset=['kode'])
            
            st.success(f"🎉 SUKSES BESAR! Total **{len(df_final)}** Analisa Pekerjaan berhasil digabung.")
            
            with st.expander("🔍 Lihat Hasil Gabungan"):
                st.dataframe(df_final)
            
            # Download
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Database Lengkap (ahsp_ciptakarya_master.csv)",
                data=csv_data,
                file_name="ahsp_ciptakarya_master.csv",
                mime="text/csv",
                type="primary"
            )
            st.info("Upload file hasil download ini ke folder `data/` di GitHub.")
            
        else:
            st.error("Tidak ada data analisa yang ditemukan. Cek kembali file yang diupload.")
