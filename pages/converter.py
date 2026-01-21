import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Mesin Konversi AHSP", page_icon="🏭")
st.title("🏭 Mesin Pencetak Database AHSP")
st.markdown("Upload file mentah (misal: `Beton.csv`), sistem akan merapikannya menjadi `ahsp_master.csv`.")

uploaded_file = st.file_uploader("Upload File CSV Mentah (Format ;)", type=['csv'])

def parse_ahsp_raw(file):
    # Baca file mentah
    content = file.getvalue().decode('utf-8', errors='ignore')
    lines = content.split('\n')
    
    data_list = []
    
    # Variabel penampung sementara
    current_kode = ""
    current_uraian = ""
    current_satuan = ""
    
    # Penampung koefisien
    temp_tenaga = []
    temp_bahan = []
    temp_alat = []
    
    # Mode penanda (sedang baca apa?)
    mode = None # Bisa 'TENAGA', 'BAHAN', 'ALAT'
    
    for line in lines:
        parts = line.split(';')
        if len(parts) < 2: continue
        
        col0 = parts[0].strip().replace('"', '')
        col1 = parts[1].strip().replace('"', '')
        
        # 1. Deteksi Judul Pekerjaan (Biasanya Kode angka di depan, misal 3.13.1)
        # Ciri: Kolom 0 ada titiknya, Kolom 1 ada teks panjang, tidak ada kata 'TENAGA/BAHAN'
        if '.' in col0 and len(col1) > 5 and 'HARGA' not in col1:
            
            # SIMPAN DATA SEBELUMNYA (JIKA ADA)
            if current_kode != "":
                data_list.append({
                    'kode': current_kode,
                    'uraian': current_uraian,
                    'satuan': current_satuan, # Satuan kadang terselip
                    'tenaga': ";".join(temp_tenaga) if temp_tenaga else "-",
                    'bahan': ";".join(temp_bahan) if temp_bahan else "-",
                    'alat': ";".join(temp_alat) if temp_alat else "-"
                })
            
            # Reset untuk item baru
            current_kode = col0
            current_uraian = col1
            current_satuan = "ls" # Default, nanti dicari kalau ada
            temp_tenaga = []
            temp_bahan = []
            temp_alat = []
            mode = None
            continue
            
        # 2. Deteksi Kategori (Tenaga/Bahan/Alat)
        if "TENAGA" in col1.upper(): mode = "TENAGA"; continue
        if "BAHAN" in col1.upper(): mode = "BAHAN"; continue
        if "PERALATAN" in col1.upper() or "ALAT" in col1.upper(): mode = "ALAT"; continue
        
        # 3. Ambil Data Koefisien
        # Struktur biasanya: No; Uraian; Satuan; Koefisien
        # Di file beton.csv kakak: Col 1=Uraian, Col 2=Satuan, Col 3=Koefisien
        if len(parts) >= 4 and mode is not None:
            nama_item = parts[1].strip()
            satuan_item = parts[2].strip()
            koef_str = parts[3].strip()
            
            # Validasi: Harus ada koefisien angka
            if koef_str and koef_str.replace('.', '').replace(',', '').isdigit():
                # Bersihkan angka (koma jadi titik)
                koef_str = koef_str.replace(',', '.')
                
                # Format: "Pasir 0.5"
                entry = f"{nama_item} {koef_str}"
                
                if mode == "TENAGA": temp_tenaga.append(entry)
                elif mode == "BAHAN": temp_bahan.append(entry)
                elif mode == "ALAT": temp_alat.append(entry)
                
                # Coba tebak satuan pekerjaan utama dari baris pekerja pertama
                if mode == "TENAGA" and current_satuan == "ls":
                     # Kadang satuan pekerjaan induk tidak tertulis jelas, kita asumsi aman
                     pass

    # Simpan item terakhir
    if current_kode != "":
        data_list.append({
            'kode': current_kode,
            'uraian': current_uraian,
            'satuan': 'ls', # Bisa diedit manual nanti
            'tenaga': ";".join(temp_tenaga) if temp_tenaga else "-",
            'bahan': ";".join(temp_bahan) if temp_bahan else "-",
            'alat': ";".join(temp_alat) if temp_alat else "-"
        })

    return pd.DataFrame(data_list)

if uploaded_file:
    st.success("File diterima! Sedang memproses...")
    try:
        df_result = parse_ahsp_raw(uploaded_file)
        
        st.write(f"✅ Berhasil mengekstrak **{len(df_result)}** Analisa Pekerjaan!")
        st.dataframe(df_result)
        
        # Tombol Download
        csv_export = df_result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Hasil (ahsp_sda_master.csv)",
            data=csv_export,
            file_name="ahsp_sda_master.csv",
            mime="text/csv"
        )
        st.info("Upload file hasil download ini ke GitHub folder 'data/'")
        
    except Exception as e:
        st.error(f"Gagal parsing: {e}")