import streamlit as st
import pandas as pd
import sys
import os

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Modul SDA (Transparan)", layout="wide")
st.title("🌊 Modul SDA (Kalkulator Transparan)")
st.caption("Rumus: (Tenaga + Bahan + Alat) + Overhead x Volume")

# ==============================
# 1. LOAD DATABASE (CSV)
# ==============================
@st.cache_data
def load_data():
    # Load AHSP
    path_ahsp = "data/ahsp_sda_master.csv"
    if os.path.exists(path_ahsp):
        try:
            df = pd.read_csv(path_ahsp, sep=None, engine='python') # Auto-detect separator
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
        if 'nama' in df_h.columns and 'harga' in df_h.columns:
            dict_harga = dict(zip(
                df_h['nama'].astype(str).str.lower().str.strip(),
                df_h['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Harga Terbaca")
    except:
        st.sidebar.error("Gagal baca CSV Harga")

# ==============================
# 3. PROSES ANALISA
# ==============================
if df_ahsp.empty:
    st.warning("⚠️ File 'data/ahsp_sda_master.csv' belum ada di GitHub/Folder Data.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("2. Pilih Pekerjaan")

# Pilihan
pilihan = st.sidebar.selectbox("Item:", df_ahsp['kode'] + " | " + df_ahsp['uraian'])
kode = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode].iloc[0]

# Volume
vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.0)

# Opsi Overhead
st.sidebar.markdown("---")
pakai_overhead = st.sidebar.checkbox("Hitung Overhead (15%)?", value=True)

# --- FUNGSI INPUT & HITUNG ---
rincian_hitung = [] # Untuk menyimpan log perhitungan

def proses_input(label, text_koef):
    subtotal_kategori = 0.0
    inputs = {}
    
    st.subheader(label)
    if pd.isna(text_koef) or str(text_koef).strip() in ["-", "nan"]:
        st.caption("- Tidak ada -")
        return 0.0

    items = str(text_koef).split(';')
    for item in items:
        import re
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        if match:
            nama = match.group(1).strip()
            koef = float(match.group(2))
            
            # Cari Harga
            kunci = nama.lower()
            harga_default = 0.0
            
            # 1. Exact Match
            if kunci in dict_harga:
                harga_default = float(dict_harga[kunci])
            # 2. Partial Match
            else:
                for k, v in dict_harga.items():
                    if k in kunci or kunci in k:
                        harga_default = float(v)
                        break
            
            # Input User
            col_a, col_b = st.columns([2, 1])
            input_harga = col_a.number_input(f"{nama}", value=harga_default, step=100.0, key=f"{kode}_{nama}")
            col_b.write(f"Koef: {koef}")
            
            # Hitung per Item
            total_item = input_harga * koef
            subtotal_kategori += total_item
            
            # Simpan ke Rincian
            rincian_hitung.append({
                "Kategori": label,
                "Komponen": nama,
                "Koefisien": koef,
                "Harga Satuan": input_harga,
                "Total (Koef x Harga)": total_item
            })
            
    st.markdown(f"**Subtotal {label}: Rp {subtotal_kategori:,.2f}**")
    return subtotal_kategori

# Layout 3 Kolom
c1, c2, c3 = st.columns(3)

with c1:
    tot_tenaga = proses_input("Tenaga", row.get('tenaga', '-'))
with c2:
    tot_bahan = proses_input("Bahan", row.get('bahan', '-'))
with c3:
    tot_alat = proses_input("Alat", row.get('alat', '-'))

# ==============================
# 4. TOTAL REKAPITULASI (RUMUS TRANSPARAN)
# ==============================
st.divider()
st.header("🧾 Rekapitulasi Harga")

# Hitung Matematika Murni
jumlah_dasar = tot_tenaga + tot_bahan + tot_alat
nilai_overhead = jumlah_dasar * 0.15 if pakai_overhead else 0
hsp_total = jumlah_dasar + nilai_overhead
grand_total = hsp_total * vol

col_res1, col_res2 = st.columns([1, 2])

with col_res1:
    st.markdown("### Rincian HSP")
    st.write(f"1. Jumlah Tenaga: **Rp {tot_tenaga:,.2f}**")
    st.write(f"2. Jumlah Bahan: **Rp {tot_bahan:,.2f}**")
    st.write(f"3. Jumlah Alat: **Rp {tot_alat:,.2f}**")
    st.markdown("---")
    st.write(f"**Jumlah (1+2+3): Rp {jumlah_dasar:,.2f}**")
    
    if pakai_overhead:
        st.write(f"Overhead (15%): Rp {nilai_overhead:,.2f}")
    else:
        st.write("Overhead: Rp 0 (Tidak dipilih)")
        
    st.success(f"**HSP (Harga Satuan): Rp {hsp_total:,.2f}**")

with col_res2:
    st.markdown("### Total Rencana Anggaran (RAB)")
    st.write(f"Volume Pekerjaan: {vol} {row['satuan']}")
    st.write(f"HSP x Volume: Rp {hsp_total:,.2f} x {vol}")
    st.markdown("### GRAND TOTAL:")
    st.header(f"Rp {grand_total:,.0f}")

# ==============================
# 5. TABEL CEK RUMUS (AUDIT)
# ==============================
with st.expander("🔍 Cek Rincian Perkalian (Audit Trail)"):
    if rincian_hitung:
        df_rincian = pd.DataFrame(rincian_hitung)
        # Format angka biar ada komanya
        st.dataframe(df_rincian.style.format({
            "Koefisien": "{:.4f}",
            "Harga Satuan": "Rp {:,.0f}",
            "Total (Koef x Harga)": "Rp {:,.2f}"
        }))
        st.info("Rumus: Total = (Koefisien x Harga Satuan)")
    else:
        st.write("Belum ada data dihitung.")
