import streamlit as st
import pandas as pd
import sys
import os

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Modul SDA (Debug Mode)", layout="wide")
st.title("🌊 Modul SDA (Mode Periksa Hitungan)")
st.caption("Kita cek satu per satu: Tenaga + Bahan + Alat")

# ==============================
# 1. LOAD DATABASE (CSV)
# ==============================
@st.cache_data
def load_data():
    path_ahsp = "data/ahsp_sda_master.csv"
    if os.path.exists(path_ahsp):
        try:
            df = pd.read_csv(path_ahsp, sep=None, engine='python') 
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df_ahsp = load_data()

# ==============================
# 2. INPUT HARGA (SIDEBAR)
# ==============================
st.sidebar.header("1. Upload Harga Satuan")
file_harga = st.sidebar.file_uploader("Upload harga.csv", type=["csv"])
dict_harga = {}

if file_harga:
    try:
        df_h = pd.read_csv(file_harga, sep=None, engine='python')
        df_h.columns = [c.strip().lower() for c in df_h.columns]
        
        # Bersihkan data harga
        if 'nama' in df_h.columns and 'harga' in df_h.columns:
            dict_harga = dict(zip(
                df_h['nama'].astype(str).str.lower().str.strip(),
                df_h['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Item Harga Terbaca")
            
            # FITUR CEK: Tampilkan 3 harga pertama untuk memastikan data masuk
            with st.sidebar.expander("Cek Sampel Harga"):
                st.write(list(dict_harga.items())[:5])
        else:
            st.sidebar.error("❌ Kolom CSV harus: 'nama' dan 'harga'")
    except Exception as e:
        st.sidebar.error(f"Gagal baca CSV: {e}")

# ==============================
# 3. PROSES ANALISA
# ==============================
if df_ahsp.empty:
    st.warning("⚠️ File database AHSP belum ada.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("2. Pilih Pekerjaan")

# Pilihan
pilihan = st.sidebar.selectbox("Item:", df_ahsp['kode'] + " | " + df_ahsp['uraian'])
kode = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode].iloc[0]

vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.0)

# ==============================
# 4. FUNGSI HITUNG PELAN-PELAN
# ==============================
def cari_harga_cerdas(nama_dicari):
    """Mencari harga dengan logika detektif"""
    kunci = nama_dicari.lower().strip()
    
    # 1. Cari Persis (Exact Match)
    if kunci in dict_harga:
        return float(dict_harga[kunci]), "✅ Persis"
    
    # 2. Cari Mirip (Partial Match)
    # Misal: Cari "Pekerja", ketemu "Pekerja (L.01)"
    for k_csv, v_csv in dict_harga.items():
        # Cek apakah nama di CSV mengandung kata kunci kita
        if kunci in k_csv: 
            return float(v_csv), f"✅ Mirip ({k_csv})"
        # Cek sebaliknya
        if k_csv in kunci:
            return float(v_csv), f"✅ Mirip ({k_csv})"
            
    return 0.0, "❌ Tidak Ketemu"

def hitung_kategori(label, text_koef):
    total_kategori = 0.0
    st.markdown(f"### {label}")
    
    if pd.isna(text_koef) or str(text_koef).strip() in ["-", "nan"]:
        st.caption("- Kosong -")
        return 0.0

    items = str(text_koef).split(';')
    
    # Tabel Rincian per Kategori
    data_tabel = []
    
    for item in items:
        import re
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        if match:
            nama = match.group(1).strip()
            koef = float(match.group(2))
            
            # CARI HARGA
            harga, status = cari_harga_cerdas(nama)
            
            # INPUT MANUAL (Jika mau koreksi)
            col_in, col_stat = st.columns([2, 1])
            harga_final = col_in.number_input(
                f"Harga {nama}", 
                value=harga, 
                step=1000.0,
                key=f"{kode}_{nama}"
            )
            col_stat.caption(f"{status}")
            
            # HITUNG: Koefisien x Harga
            subtotal = koef * harga_final
            total_kategori += subtotal
            
            data_tabel.append({
                "Komponen": nama,
                "Koefisien": koef,
                "Harga": harga_final,
                "Subtotal": subtotal
            })
    
    # Tampilkan Hasil Hitungan Kategori Ini
    if data_tabel:
        st.info(f"💰 Total {label}: Rp {total_kategori:,.2f}")
    
    return total_kategori

# ==============================
# 5. TAMPILAN UTAMA (3 KOLOM)
# ==============================
c1, c2, c3 = st.columns(3)

with c1:
    # HITUNG TENAGA
    tot_1 = hitung_kategori("1. TENAGA", row.get('tenaga', '-'))

with c2:
    # HITUNG BAHAN
    tot_2 = hitung_kategori("2. BAHAN", row.get('bahan', '-'))

with c3:
    # HITUNG ALAT
    tot_3 = hitung_kategori("3. ALAT", row.get('alat', '-'))

# ==============================
# 6. PENJUMLAHAN AKHIR (TRANSARAN)
# ==============================
st.divider()
st.header("🧮 Pengecekan Total (1 + 2 + 3)")

col_kiri, col_kanan = st.columns([2, 1])

with col_kiri:
    st.write("Mari kita jumlahkan angkanya:")
    st.code(f"""
    1. Total Tenaga : Rp {tot_1:,.2f}
    2. Total Bahan  : Rp {tot_2:,.2f}
    3. Total Alat   : Rp {tot_3:,.2f}
    -------------------------------- +
    JUMLAH DASAR    : Rp {(tot_1 + tot_2 + tot_3):,.2f}
    """)
    
    # Overhead
    st.write("**Hitungan Overhead & Profit:**")
    pakai_oh = st.checkbox("Tambahkan 15%?", value=True)
    
    jumlah_dasar = tot_1 + tot_2 + tot_3
    nilai_oh = jumlah_dasar * 0.15 if pakai_oh else 0
    hsp_final = jumlah_dasar + nilai_oh
    
    st.code(f"""
    Jumlah Dasar    : Rp {jumlah_dasar:,.2f}
    Overhead (15%)  : Rp {nilai_oh:,.2f}
    -------------------------------- +
    HARGA SATUAN    : Rp {hsp_final:,.2f}
    """)

with col_kanan:
    st.metric("GRAND TOTAL (RAB)", f"Rp {(hsp_final * vol):,.0f}")
    st.caption(f"Volume: {vol} {row['satuan']}")

# Debug Alert
if tot_1 == 0 and tot_2 == 0 and tot_3 == 0:
    st.error("⚠️ SEMUA TOTAL 0? Kemungkinan nama di CSV Harga tidak cocok dengan Database.")
elif tot_1 == 0:
    st.warning("⚠️ Total Tenaga 0. Cek apakah harga 'Pekerja' / 'Tukang' sudah masuk di CSV?")
