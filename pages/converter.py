import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Mesin Konversi Universal", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP")
st.caption("Support: CSV & Excel (Multi-Sheet)")

# ==========================================
# 1. CORE ENGINE (LOGIKA PEMBACAAN)
# ==========================================

def parse_sda_complex(lines):
    """Membaca format SDA yang rumit (Ada Koefisien)"""
    data_list = []
    current_data = {'kode': '', 'uraian': '', 'satuan': 'ls', 'tenaga': [], 'bahan': [], 'alat': []}
    mode = None 
    
    for line in lines:
        # Pisahkan berdasarkan titik koma (CSV style)
        parts = line.split(';')
        parts = [p.strip().replace('"', '').replace('nan', '') for p in parts] # Bersihkan 'nan' dari Excel
        
        if len(parts) < 2: continue
        
        # Deteksi Kode (Kolom 0) -> Contoh: 3.13.1
        if re.match(r'^\d+\.\d+', parts[0]) and len(parts[1]) > 3:
            if current_data['kode']:
                data_list.append(export_item(current_data))
            
            current_data = {
                'kode': parts[0], 'uraian': parts[1], 'satuan': 'ls',
                'tenaga': [], 'bahan': [], 'alat': []
            }
            mode = None
            continue

        # Deteksi Mode (Tenaga/Bahan/Alat)
        col_str = "".join(parts[:2]).upper()
        if "TENAGA" in col_str: mode = 'tenaga'; continue
        if "BAHAN" in col_str: mode = 'bahan'; continue
        if "ALAT" in col_str or "PERALATAN" in col_str: mode = 'alat'; continue
        
        # Ambil Koefisien
        if mode and len(parts) >= 4:
            # Kolom 3 biasanya koefisien
            clean_koef = parts[3].replace('.', '').replace(',', '.')
            if clean_koef.replace('.', '', 1).isdigit() and float(clean_koef) > 0:
                item_str = f"{parts[1]} {clean_koef}"
                if mode == 'tenaga': current_data['tenaga'].append(item_str)
                elif mode == 'bahan': current_data['bahan'].append(item_str)
                elif mode == 'alat': current_data['alat'].append(item_str)

    if current_data['kode']: data_list.append(export_item(current_data))
    return data_list

def parse_cipta_karya(lines):
    """Membaca format Cipta Karya (Hanya Daftar Harga)"""
    data_list = []
    for line in lines:
        parts = line.split(';')
        parts = [p.strip().replace('"', '') for p in parts]
        if len(parts) < 4: continue
        
        if re.match(r'^[A-Z0-9]+\.[0-9\.]+', parts[1]):
            data_list.append({
                'kode': parts[1], 'uraian': parts[2], 'satuan': parts[3],
                'tenaga': '-', 'bahan': '-', 'alat': '-'
            })
    return data_list

def export_item(d):
    return {
        'kode': d['kode'], 'uraian': d['uraian'], 'satuan': d['satuan'],
        'tenaga': ";".join(d['tenaga']) if d['tenaga'] else "-",
        'bahan': ";".join(d['bahan']) if d['bahan'] else "-",
        'alat': ";".join(d['alat']) if d['alat'] else "-"
    }

# ==========================================
# 2. UI & HANDLING FILE
# ==========================================

# Pilihan Mode
mode_konversi = st.radio(
    "Pilih Jenis File:",
    ["1. Format SDA (Detail Analisa)", 
     "2. Format Cipta Karya (Rekap Harga)"]
)

uploaded_file = st.file_uploader("Upload File (CSV atau Excel .xlsx)", type=['csv', 'xlsx'])

if uploaded_file:
    with st.spinner("Sedang membongkar file..."):
        try:
            all_lines = []
            file_name = uploaded_file.name
            
            # --- JIKA FILE EXCEL (.xlsx) ---
            if file_name.endswith('.xlsx'):
                st.info("📂 Terdeteksi file Excel. Sedang membaca seluruh Sheet...")
                
                # Baca Excel tanpa header (header=None) biar semua baris terbaca
                xls = pd.ExcelFile(uploaded_file)
                
                total_sheets = len(xls.sheet_names)
                my_bar = st.progress(0)
                
                for i, sheet_name in enumerate(xls.sheet_names):
                    # Update progress bar
                    my_bar.progress((i + 1) / total_sheets)
                    
                    # Baca sheet menjadi DataFrame
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    
                    # Ubah setiap baris menjadi string yang dipisah titik koma (mirip CSV)
                    # Contoh: "3.1;Galian;m3" -> "3.1;Galian;m3"
                    sheet_lines = df.fillna('').astype(str).apply(lambda x: ';'.join(x), axis=1).tolist()
                    all_lines.extend(sheet_lines)
                    
                st.success(f"✅ Berhasil menggabungkan **{total_sheets} Sheet**!")
                
            # --- JIKA FILE CSV (.csv) ---
            else:
                content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                all_lines = content.split('\n')

            # --- PROSES KONVERSI ---
            if "Format SDA" in mode_konversi:
                hasil = parse_sda_complex(all_lines)
                filename = "ahsp_sda_master.csv"
            else:
                hasil = parse_cipta_karya(all_lines)
                filename = "ahsp_ciptakarya_master.csv"
            
            df_hasil = pd.DataFrame(hasil)
            
            # --- TAMPILKAN HASIL ---
            if not df_hasil.empty:
                st.success(f"🎉 SELESAI! Ditemukan **{len(df_hasil)}** Item Pekerjaan.")
                
                with st.expander("👁️ Cek Sampel Data"):
                    st.dataframe(df_hasil.head(50))
                
                # Download Button
                csv_data = df_hasil.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.error("❌ Data kosong. Pastikan format kolom Excel sesuai.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
