import streamlit as st
import pandas as pd
import os

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Modul SDA (Final)", layout="wide")
st.title("🌊 Modul SDA (Penyusunan RAB)")

# Inisialisasi Keranjang RAB (Session State)
if "rab_list" not in st.session_state:
    st.session_state.rab_list = []

# ==============================
# 1. LOAD DATABASE (Master AHSP dari GitHub)
# ==============================
@st.cache_data
def load_ahsp():
    path = "data/ahsp_sda_master.csv"
    if os.path.exists(path):
        try:
            # Baca CSV engine python (Auto-detect separator)
            df = pd.read_csv(path, sep=None, engine='python')
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df_ahsp = load_ahsp()

# ==============================
# 2. UPLOAD HARGA (Dari Komputer User)
# ==============================
st.sidebar.header("1. Upload Harga (Wajib)")
file_harga = st.sidebar.file_uploader("Upload harga_fix.csv", type=["csv"])
dict_harga = {}

if file_harga:
    try:
        df_h = pd.read_csv(file_harga, sep=None, engine='python')
        df_h.columns = [c.strip().lower() for c in df_h.columns]
        if 'nama' in df_h.columns and 'harga' in df_h.columns:
            # Buat kamus harga
            dict_harga = dict(zip(
                df_h['nama'].astype(str).str.lower().str.strip(),
                df_h['harga']
            ))
            st.sidebar.success(f"✅ {len(dict_harga)} Harga Masuk")
        else:
            st.sidebar.error("❌ CSV Harga salah format (harus ada kolom 'nama' dan 'harga')")
    except:
        st.sidebar.error("Gagal baca CSV Harga")
else:
    st.sidebar.warning("⚠️ Upload harga dulu biar tidak Rp 0!")

# ==============================
# 3. PILIH PEKERJAAN
# ==============================
if df_ahsp.empty:
    st.error("⚠️ Database AHSP belum ada di GitHub (data/ahsp_sda_master.csv).")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("2. Input Pekerjaan")

# Dropdown Pilihan
pilihan = st.sidebar.selectbox("Pilih Item:", df_ahsp['kode'] + " | " + df_ahsp['uraian'])
kode = pilihan.split(" | ")[0]
row = df_ahsp[df_ahsp['kode'] == kode].iloc[0]

# Input Volume
vol = st.sidebar.number_input(f"Volume ({row['satuan']})", value=1.0, min_value=0.1)

# ==============================
# 4. ENGINE HITUNG (Detektif Harga)
# ==============================
def cari_harga(nama_item):
    kunci = nama_item.lower().strip()
    
    # 1. Cari Persis (Prioritas)
    if kunci in dict_harga:
        return float(dict_harga[kunci]), True
    
    # 2. Cari Mirip (Cadangan)
    for k, v in dict_harga.items():
        if k in kunci or kunci in k:
            return float(v), True
            
    return 0.0, False # Tidak ketemu

def hitung_komponen(label, text_data):
    total = 0.0
    detail_html = ""
    
    if pd.isna(text_data) or str(text_data).strip() in ["-", "nan"]:
        return 0.0, "<small>- Tidak ada -</small>"

    items = str(text_data).split(';')
    for item in items:
        import re
        match = re.search(r'^(.*?)\s+([\d\.]+)', item.strip())
        if match:
            nama = match.group(1).strip()
            koef = float(match.group(2))
            
            harga, ketemu = cari_harga(nama)
            subtotal = koef * harga
            total += subtotal
            
            # Status Warna: Merah kalau 0 (Tidak ketemu), Hijau kalau OK
            warna = "green" if ketemu else "red"
            status_text = f"✅ Rp {harga:,.0f}" if ketemu else "❌ <b>(Gagal Baca)</b>"
            
            detail_html += f"""
            <div style="margin-bottom: 5px; border-bottom: 1px solid #eee;">
                <b>{nama}</b> <span style="color:{warna};">({status_text})</span><br>
                {koef} x {harga:,.0f} = <b>Rp {subtotal:,.0f}</b>
            </div>
            """
    return total, detail_html

# ==============================
# 5. TAMPILAN ANALISA (KARTU)
# ==============================
st.subheader(f"Analisa: {row['uraian']}")

c1, c2, c3 = st.columns(3)

with c1:
    st.info("👷 TENAGA")
    tot_tenaga, html_tenaga = hitung_komponen("Tenaga", row.get('tenaga', '-'))
    st.markdown(html_tenaga, unsafe_allow_html=True)
    st.markdown(f"**Subtotal: Rp {tot_tenaga:,.0f}**")

with c2:
    st.warning("🧱 BAHAN")
    tot_bahan, html_bahan = hitung_komponen("Bahan", row.get('bahan', '-'))
    st.markdown(html_bahan, unsafe_allow_html=True)
    st.markdown(f"**Subtotal: Rp {tot_bahan:,.0f}**")

with c3:
    st.success("🚜 ALAT")
    tot_alat, html_alat = hitung_komponen("Alat", row.get('alat', '-'))
    st.markdown(html_alat, unsafe_allow_html=True)
    st.markdown(f"**Subtotal: Rp {tot_alat:,.0f}**")

# Hitungan Akhir
jumlah_dasar = tot_tenaga + tot_bahan + tot_alat
overhead = jumlah_dasar * 0.15
hsp = jumlah_dasar + overhead
total_harga = hsp * vol

# Tampilkan Angka Besar
st.divider()
col_kiri, col_kanan = st.columns([2, 1])

with col_kiri:
    if jumlah_dasar == 0:
        st.error("⚠️ Total Rp 0. Cek tanda ❌ di atas. Nama di CSV Harga harus sama dengan nama Bahan.")
    else:
        st.write(f"HSP (Dasar + 15% OH): **Rp {hsp:,.2f}**")
        st.write(f"Volume: {vol} {row['satuan']}")
        
with col_kanan:
    st.metric("TOTAL HARGA", f"Rp {total_harga:,.0f}")
    
    # TOMBOL TAMBAH KE RAB
    if st.button("➕ Tambah ke Daftar RAB", type="primary", use_container_width=True):
        if total_harga > 0:
            st.session_state.rab_list.append({
                "Kode": row['kode'],
                "Uraian": row['uraian'],
                "Volume": vol,
                "Satuan": row['satuan'],
                "HSP": hsp,
                "Total": total_harga
            })
            st.success("Berhasil ditambahkan ke bawah! 👇")
        else:
            st.error("Harga masih 0, tidak bisa disimpan.")

# ==============================
# 6. TABEL REKAP RAB (KERANJANG)
# ==============================
st.markdown("---")
st.header("📋 Daftar RAB (Bill of Quantities)")

if st.session_state.rab_list:
    df_rab = pd.DataFrame(st.session_state.rab_list)
    
    st.dataframe(
        df_rab, 
        use_container_width=True,
        column_config={
            "HSP": st.column_config.NumberColumn(format="Rp %.2f"),
            "Total": st.column_config.NumberColumn(format="Rp %.2f")
        }
    )
    
    # Grand Total
    grand_total_rab = df_rab['Total'].sum()
    st.metric("GRAND TOTAL PROYEK", f"Rp {grand_total_rab:,.0f}")
    
    # Tombol Reset
    if st.button("🗑️ Hapus Semua Data"):
        st.session_state.rab_list = []
        st.rerun()
else:
    st.info("Belum ada item pekerjaan yang ditambahkan.")
