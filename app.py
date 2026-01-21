# ==============================
# LOAD DATABASE (VERSI AUTO-SEARCH SHEET)
# ==============================
@st.cache_data
def load_database():
    path = "data/ahsp_sda_2025_tanah_manual_core_template.xlsx"
    
    if not os.path.exists(path):
        st.error(f"File database tidak ditemukan di: {path}")
        st.stop()
    
    try:
        # 1. Buka File Excel (Tanpa membaca isinya dulu)
        xls = pd.ExcelFile(path)
        
        # 2. Cek SEMUA nama sheet yang ada
        sheet_names = xls.sheet_names
        st.sidebar.success(f"📂 Sheet ditemukan: {sheet_names}") # Info buat debug
        
        target_df = pd.DataFrame()
        found = False
        
        # 3. Loop: Cari satu-satu sheet mana yang punya kolom 'kode_ahsp'
        for sheet in sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            
            # Bersihkan nama kolom (hapus spasi, huruf kecil)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            
            # APAKAH INI SHEET YANG KITA CARI?
            if "kode_ahsp" in df.columns:
                target_df = df
                found = True
                break # Ketemu! Berhenti mencari.
        
        if not found:
            st.error("🚨 Gagal menemukan data! Tidak ada sheet yang memiliki kolom 'kode_ahsp'.")
            st.write("Daftar Sheet di file ini:", sheet_names)
            st.write("Coba cek apakah nama kolom di Excel sudah benar 'kode_ahsp'?")
            st.stop()
            
        return target_df

    except Exception as e:
        st.error(f"Error membaca Excel: {e}")
        st.stop()
