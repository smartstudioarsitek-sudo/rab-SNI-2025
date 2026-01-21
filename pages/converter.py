import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Mesin Konversi Universal", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP")
st.caption("Support: Format Analisa SDA (Detail) & Format Cipta Karya (Rekap)")

# Pilihan Mode
mode_konversi = st.radio(
    "Pilih Jenis File yang Diupload:",
    ["1. Format SDA/Beton (Ada rincian Koefisien)", 
     "2. Format Cipta Karya (Hanya Daftar Harga Jadi)"]
)

uploaded_file = st.file_uploader("Upload File CSV Mentah", type=['csv'])

# --- FUNGSI 1: PARSING SDA (DETAIL) ---
def parse_sda_complex(lines):
    data_list = []
    current_data = {'kode': '', 'uraian': '', 'satuan': 'ls', 'tenaga': [], 'bahan': [], 'alat': []}
    mode = None 
    
    for line in lines:
        parts = line.split(';')
        parts = [p.strip().replace('"', '') for p in parts]
        if len(parts) < 2: continue
        
        # Deteksi Kode (Kolom 0)
        if re.match(r'^\d+\.\d+', parts[0]) and len(parts[1]) > 3:
            if current_data['kode']:
                data_list.append(export_item(current_data))
            
            current_data = {
                'kode': parts[0], 'uraian': parts[1], 'satuan': 'ls',
                'tenaga': [], 'bahan': [], 'alat': []
            }
            mode = None
            continue

        # Deteksi Mode
        col_str = "".join(parts[:2]).upper()
        if "TENAGA" in col_str: mode = 'tenaga'; continue
        if "BAHAN" in col_str: mode = 'bahan'; continue
        if "ALAT" in col_str or "PERALATAN" in col_str: mode = 'alat'; continue
        
        # Ambil Koefisien
        if mode and len(parts) >= 4:
            clean_koef = parts[3].replace('.', '').replace(',', '.')
            if clean_koef.replace('.', '', 1).isdigit():
                item_str = f"{parts[1]} {clean_koef}"
                if mode == 'tenaga': current_data['tenaga'].append(item_str)
                elif mode == 'bahan': current_data['bahan'].append(item_str)
                elif mode == 'alat': current_data['alat'].append(item_str)

    if current_data['kode']: data_list.append(export_item(current_data))
    return data_list

# --- FUNGSI 2: PARSING CIPTA KARYA (REKAP) ---
def parse_cipta_karya(lines):
    data_list = []
    
    for line in lines:
        # Cipta Karya format: ;Kode;Uraian;Satuan;Harga;...
        parts = line.split(';')
        parts = [p.strip().replace('"', '') for p in parts]
        
        # Minimal harus ada sampai kolom Satuan (index 3)
        if len(parts) < 4: continue
        
        # Cek apakah Kolom 1 adalah Kode (misal: 1.1.1.1 atau A.2.3)
        # Regex: Angka titik Angka
        kode_potensial = parts[1]
        
        if re.match(r'^[A-Z0-9]+\.[0-9\.]+', kode_potensial):
            # INI ADALAH ITEM PEKERJAAN
            kode = parts[1]
            uraian = parts[2]
            satuan = parts[3]
            
            # Karena tidak ada rincian, kita kosongkan komponennya
            # User nanti harus input manual analisa kalau mau detail
            
            data_list.append({
                'kode': kode,
                'uraian': uraian,
                'satuan': satuan,
                'tenaga': '-', # Data tidak tersedia di file rekap
                'bahan': '-',
                'alat': '-'
            })
            
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

# --- UI UTAMA ---
if uploaded_file:
    with st.spinner("Sedang menyedot data..."):
        try:
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            lines = content.split('\n')
            
            if "Format SDA" in mode_konversi:
                hasil = parse_sda_complex(lines)
                filename = "ahsp_sda_master.csv"
            else:
                hasil = parse_cipta_karya(lines)
                filename = "ahsp_ciptakarya_master.csv"
            
            df_hasil = pd.DataFrame(hasil)
            
            if not df_hasil.empty:
                st.success(f"✅ BERHASIL! Ditemukan **{len(df_hasil)}** Item Pekerjaan.")
                
                # Preview
                with st.expander("👁️ Cek Sampel Data"):
                    st.dataframe(df_hasil.head(100))
                
                if "Format Cipta Karya" in mode_konversi:
                    st.warning("⚠️ Catatan: File Cipta Karya ini hanya berisi DAFTAR ITEM. Kolom Tenaga/Bahan/Alat kosong karena di file aslinya tidak ada rincian resepnya.")

                # Download
                csv_data = df_hasil.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.error("❌ Tidak ada data yang terbaca. Cek apakah format file sesuai pilihan mode.")
                
        except Exception as e:
            st.error(f"Error: {e}")
