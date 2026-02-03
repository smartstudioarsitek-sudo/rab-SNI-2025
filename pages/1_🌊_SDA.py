import streamlit as st
import pandas as pd
import io

# Import Engine (Pastikan file sda_engine.py yang baru sudah ada di folder engine)
try:
    from engine import sda_engine
except ImportError:
    st.error("🚨 File engine/sda_engine.py tidak ditemukan!")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Modul SDA (Lite)", page_icon="🌊", layout="wide")
st.title("🌊 Modul SDA (Simple Mode)")
st.caption("Mode Input Fleksibel: Gunakan Data Bawaan atau Upload Data Proyek Sendiri")

# Init Session State
if "boq_sda" not in st.session_state:
    st.session_state.boq_sda = []

# ==========================================
# 1. DATABASE CERDAS (ON-THE-FLY)
# ==========================================
def get_default_data():
    """
    Membuat data dummy otomatis agar aplikasi tidak kosong/error
    saat database Excel belum siap.
    """
    data = [
        {
            "kode": "T.01", 
            "uraian": "Galian Tanah Biasa (Manual)", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 0.750, "Mandor": 0.025},
            "bahan": {},
            "alat": {}
        },
        {
            "kode": "P.01", 
            "uraian": "Pasangan Batu Kali 1:4", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 1.500, "Tukang Batu": 0.750, "Mandor": 0.075},
            "bahan": {"Batu Kali": 1.200, "Semen": 163.00, "Pasir": 0.520},
            "alat": {}
        },
        {
            "kode": "B.05", 
            "uraian": "Beton K-175 (Manual)", 
            "satuan": "m3",
            "tenaga": {"Pekerja": 1.650, "Tukang Batu": 0.275, "Mandor": 0.083},
            "bahan": {"Semen": 326.00, "Pasir": 0.760, "Kerikil": 1.029},
            "alat": {}
        }
    ]
    return pd.DataFrame(data)

# --- SIDEBAR: PILIH SUMBER DATA ---
st.sidebar.header("📂 Sumber Data Analisa")
pilihan_sumber = st.sidebar.radio(
    "Pilih Database:",
    ["Gunakan Data Contoh (Default)", "Upload Excel Proyek"]
)

df_ahsp = pd.DataFrame()

if pilihan_sumber == "Gunakan Data Contoh (Default)":
    df_ahsp = get_default_data()
    st.sidebar.success("✅ Menggunakan 3 Data Contoh (Aman)")
else:
    file_user = st.sidebar.file_uploader("Upload Excel Analisa (Format Custom)", type=["xlsx"])
    if file_user:
        try:
            # Baca Excel user (Asumsi kolom sederhana)
            df_ahsp = pd.read_excel(file_user)
            st.sidebar.success(f"✅ Terload: {len(df_ahsp)} item")
        except:
            st.sidebar.error("Format Excel tidak terbaca.")
    else:
        st.sidebar.info("Silakan upload file, atau kembali ke mode Default.")

# ==========================================
# 2. INPUT HARGA SATUAN (SHS)
# ==========================================
st.sidebar.divider()
st.sidebar.header("💰 Harga Dasar (SHS)")
# Default harga agar user tidak capek ngetik di awal
default_harga = {
    "Pekerja": 100000, "Mandor": 150000, "Tukang Batu": 120000,
    "Semen": 1300, "Pasir": 250000, "Batu Kali": 300000, "Kerikil": 280000
}

# Opsi Upload Harga
upload_harga = st.sidebar.file_uploader("Upload File Harga (Opsional)", type=["xlsx", "csv"])
harga_final = default_harga.copy()

if upload_harga:
    # Logika baca file harga (sederhana)
    try:
        df_h = pd.read_csv(upload_harga) if upload_harga.name.endswith('csv') else pd.read_excel(upload_harga)
        # Asumsi kolom 0 = nama, kolom 1 = harga
        new_prices = dict(zip(df_h.iloc[:,0], df_h.iloc[:,1]))
        harga_final.update(new_prices)
        st.sidebar.success(f"Harga terupdate: {len(new_prices)} item")
    except:
        pass

# Tampilkan Editor Harga (Agar user bisa ubah manual)
with st.sidebar.expander("📝 Edit Harga Manual"):
    harga_final["Pekerja"] = st.number_input("Upah Pekerja", value=harga_final.get("Pekerja", 0))
    harga_final["Semen"] = st.number_input("Harga Semen (per Kg)", value=harga_final.get("Semen", 0))
    # Tambahkan input lain sesuai kebutuhan

# ==========================================
# 3. AREA KERJA UTAMA
# ==========================================

if df_ahsp.empty:
    st.warning("Belum ada data analisa. Pilih 'Gunakan Data Contoh' di sidebar.")
else:
    # --- PILIH ITEM PEKERJAAN ---
    pilihan_item = st.selectbox(
        "🛠️ Pilih Item Pekerjaan:",
        df_ahsp['uraian'].tolist()
    )
    
    # Ambil data lengkap item yang dipilih
    row = df_ahsp[df_ahsp['uraian'] == pilihan_item].iloc[0]
    
    col_vol, col_sat = st.columns([1,1])
    vol = col_vol.number_input("Volume", value=1.0, step=0.1)
    sat = col_sat.text_input("Satuan", value=row['satuan'], disabled=True)

    # --- RINCIAN KOEFISIEN (Display Only) ---
    with st.expander("🔍 Lihat Koefisien Analisa"):
        c1, c2 = st.columns(2)
        c1.write("**Tenaga:**")
        c1.json(row['tenaga']) # Menampilkan dictionary koefisien
        c2.write("**Bahan:**")
        c2.json(row['bahan'])

    # --- HITUNG DENGAN ENGINE ---
    if st.button("➕ Masukkan ke RAB"):
        # Mapping harga otomatis (Case Insensitive sederhana)
        def match_price(nama_item):
            # Cari nama yang mirip di dictionary harga
            for k, v in harga_final.items():
                if k.lower() in str(nama_item).lower():
                    return v
            return 0

        # Siapkan dict harga spesifik untuk item ini
        h_tenaga = {k: match_price(k) for k in row['tenaga']}
        h_bahan = {k: match_price(k) for k in row['bahan']}
        h_alat = {k: match_price(k) for k in row['alat']}

        # Panggil Engine (Jantung Aplikasi)
        hasil = sda_engine.hitung_rab_lengkap(
            kode_ahsp=row['kode'],
            uraian=row['uraian'],
            volume=vol,
            satuan=row['satuan'],
            koef_tenaga=row['tenaga'], harga_tenaga=h_tenaga,
            koef_bahan=row['bahan'], harga_bahan=h_bahan,
            koef_alat=row['alat'], harga_alat=h_alat,
            persen_overhead=15.0
        )
        
        st.session_state.boq_sda.append(hasil)
        st.success("Item tersimpan!")

# ==========================================
# 4. TABEL OUTPUT (RAB)
# ==========================================
st.divider()
st.subheader("📋 Rekapitulasi Biaya")

if st.session_state.boq_sda:
    # Konversi ke Dataframe untuk tampilan tabel
    data_tabel = []
    for item in st.session_state.boq_sda:
        data_tabel.append({
            "Uraian": item['meta']['uraian'],
            "Vol": item['meta']['volume'],
            "Sat": item['meta']['satuan'],
            "HSP (Rp)": item['biaya']['hsp'],
            "Total (Rp)": item['biaya']['total_final']
        })
    
    df_view = pd.DataFrame(data_tabel)
    st.dataframe(
        df_view, 
        use_container_width=True,
        column_config={
            "HSP (Rp)": st.column_config.NumberColumn(format="Rp %.0f"),
            "Total (Rp)": st.column_config.NumberColumn(format="Rp %.0f")
        }
    )
    
    grand_total = df_view['Total (Rp)'].sum()
    st.markdown(f"### 💰 Total Proyek: **Rp {grand_total:,.0f}**")
    
    # Tombol Download Excel
    xlsx = sda_engine.export_to_excel(df_view) # Error disini jika struktur DF beda, tapi aman utk skrg
    st.download_button("📥 Download Excel", xlsx, "RAB_Simple.xlsx")
    
else:
    st.info("RAB masih kosong. Silakan tambah item pekerjaan di atas.")
