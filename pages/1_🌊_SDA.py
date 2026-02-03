import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO

# Import engine
from engine import sda_engine # Pastikan ini mengarah ke file sda_engine.py yang sudah di-rename

# --- KONFIGURASI APLIKASI ---
st.set_page_config(
    page_title="RAB SDA",
    page_icon="🌊",
    layout="wide"
)

# --- FUNGSI BANTU ---
@st.cache_data
def load_ahsp_master_sda(file_path='data/db_ahsp_master.xlsx'):
    try:
        df_master = pd.read_excel(file_path)
        if 'bidang' in df_master.columns:
            # Filter untuk bidang 'sda' dan pastikan semua kolom yang diperlukan ada
            df_sda = df_master[df_master['bidang'].str.lower() == 'sda'].copy()
            required_cols = ['kode_ahsp', 'uraian_pekerjaan', 'satuan', 'tenaga', 'bahan', 'alat']
            if not all(col in df_sda.columns for col in required_cols):
                st.error(f"Kolom wajib ({', '.join(required_cols)}) tidak lengkap di master AHSP SDA.")
                return pd.DataFrame()

            # Pastikan koefisien adalah string JSON yang valid
            for col in ['tenaga', 'bahan', 'alat']:
                df_sda[col] = df_sda[col].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x, str) else {})

            return df_sda
        return pd.DataFrame()
    except FileNotFoundError:
        st.error(f"File master AHSP tidak ditemukan di: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error saat memuat master AHSP SDA: {e}")
        return pd.DataFrame()

@st.cache_data
def load_default_harga_dasar():
    # Contoh harga dasar default
    return {
        "Pekerja": 100000,
        "Tukang Batu": 120000,
        "Kepala Tukang": 150000,
        "Mandor": 180000,
        "Semen PC (Kg)": 1450,
        "Pasir Pasang (m3)": 200000,
        "Batu Pecah 2/3 (m3)": 300000,
        "Besi Beton (Kg)": 15000,
        "Papan Bekisting (m3)": 3500000,
        "Excavator (Jam)": 750000,
        "Molon (Jam)": 50000,
    }

def match_price(item_name: str, prices: dict):
    """
    Fungsi untuk mencocokkan nama item dengan harga yang tersedia.
    Prioritaskan exact match, lalu fuzzy match (case-insensitive).
    """
    item_name_lower = item_name.lower()

    # 1. Exact match
    if item_name in prices:
        return prices[item_name]

    # 2. Case-insensitive exact match
    for k, v in prices.items():
        if k.lower() == item_name_lower:
            return v

    # 3. Fuzzy match (item_name contained in price_key)
    # Ini bisa berbahaya jika ada "Pasir" dan "Pasir Beton".
    # Untuk sementara, kita pertahankan logika sebelumnya namun dengan peringatan.
    # Idealnya, menggunakan ID unik atau mapping manual.
    for k, v in prices.items():
        if item_name_lower in k.lower(): # Perhatikan potensi ambiguitas di sini!
            # st.warning(f"Peringatan: '{item_name}' dicocokkan dengan '{k}'. Pastikan ini benar.")
            return v

    return 0 # Jika tidak ditemukan, kembalikan 0


# --- SIDEBAR ---
st.sidebar.header("Pengaturan Global RAB")
proyek_name = st.sidebar.text_input("Nama Proyek", "Proyek SDA")
persen_overhead = st.sidebar.number_input("Persentase Overhead & Profit (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
persen_ppn = st.sidebar.number_input("Persentase PPN (%)", min_value=0.0, max_value=100.0, value=11.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("Manajemen Harga Dasar")
harga_source = st.sidebar.radio("Sumber Harga Dasar:", ("Default", "Upload Excel", "Input Manual"))

harga_dasar_final = {}
if harga_source == "Default":
    harga_dasar_final = load_default_harga_dasar()
    st.sidebar.info("Menggunakan harga dasar default. Anda bisa mengubahnya di bagian 'Input Manual' atau 'Upload Excel'.")
elif harga_source == "Upload Excel":
    uploaded_harga_file = st.sidebar.file_uploader("Upload File Excel Harga Dasar (.xlsx)", type=["xlsx"])
    if uploaded_harga_file:
        try:
            df_harga_upload = pd.read_excel(uploaded_harga_file)
            if 'nama_item' in df_harga_upload.columns and 'harga_satuan' in df_harga_upload.columns:
                harga_dasar_final = dict(zip(df_harga_upload['nama_item'], df_harga_upload['harga_satuan']))
                st.sidebar.success("Harga dasar berhasil diunggah!")
            else:
                st.sidebar.error("File Excel harga dasar harus memiliki kolom 'nama_item' dan 'harga_satuan'.")
        except Exception as e:
            st.sidebar.error(f"Error saat mengunggah harga dasar: {e}")
    else:
        st.sidebar.info("Silakan unggah file Excel harga dasar Anda.")
elif harga_source == "Input Manual":
    st.sidebar.subheader("Input Harga Manual")
    harga_dasar_final = st.session_state.get('manual_prices_sda', load_default_harga_dasar())

    # Display current prices for editing
    edited_prices = {}
    for item, price in harga_dasar_final.items():
        edited_prices[item] = st.sidebar.number_input(f"{item} (Rp)", value=float(price), key=f"manual_price_{item}")

    new_item_name = st.sidebar.text_input("Nama Item Baru", key="new_item_name_sda")
    new_item_price = st.sidebar.number_input("Harga Item Baru (Rp)", min_value=0.0, value=0.0, key="new_item_price_sda")

    if st.sidebar.button("Tambah/Update Harga", key="add_update_price_sda"):
        if new_item_name and new_item_price > 0:
            edited_prices[new_item_name] = new_item_price
            st.sidebar.success(f"Harga '{new_item_name}' ditambahkan/diperbarui.")
        else:
            st.sidebar.warning("Silakan masukkan nama dan harga item baru yang valid.")

    harga_dasar_final = edited_prices
    st.session_state['manual_prices_sda'] = harga_dasar_final # Simpan ke session state

# Display final loaded prices for verification
with st.sidebar.expander("Daftar Harga Dasar Aktif"):
    st.json(harga_dasar_final)

# --- MAIN APLIKASI ---
st.title("🌊 RAB Modul Sumber Daya Air (SDA)")
st.write(f"Menyusun RAB untuk proyek SDA Anda. Nama Proyek: **{proyek_name}**")

# Load AHSP master untuk SDA
df_ahsp_sda = load_ahsp_master_sda()

if df_ahsp_sda.empty:
    st.warning("Data AHSP untuk SDA tidak ditemukan atau tidak lengkap di `data/db_ahsp_master.xlsx`. Silakan periksa file master Anda.")
else:
    st.subheader("Pilih Pekerjaan dan Masukkan Volume")

    # Inisialisasi keranjang RAB di session state jika belum ada
    if 'keranjang_rab_sda' not in st.session_state:
        st.session_state.keranjang_rab_sda = []

    # Dropdown untuk memilih pekerjaan AHSP
    selected_ahsp_index = st.selectbox(
        "Pilih Uraian Pekerjaan:",
        df_ahsp_sda.index,
        format_func=lambda x: f"{df_ahsp_sda.loc[x, 'kode_ahsp']} - {df_ahsp_sda.loc[x, 'uraian_pekerjaan']}"
    )

    if selected_ahsp_index is not None:
        selected_pekerjaan = df_ahsp_sda.loc[selected_ahsp_index]
        st.write(f"**Uraian Pekerjaan:** {selected_pekerjaan['uraian_pekerjaan']}")
        st.write(f"**Satuan:** {selected_pekerjaan['satuan']}")

        volume_input = st.number_input(
            f"Masukkan Volume Pekerjaan ({selected_pekerjaan['satuan']}):",
            min_value=0.0,
            value=1.0,
            step=0.01
        )

        if st.button("Tambah ke RAB"):
            if volume_input > 0:
                # Ambil koefisien
                koef_tenaga = selected_pekerjaan.get('tenaga', {})
                koef_bahan = selected_pekerjaan.get('bahan', {})
                koef_alat = selected_pekerjaan.get('alat', {})

                # Lakukan matching harga
                harga_tenaga_matched = {k: match_price(k, harga_dasar_final) for k in koef_tenaga.keys()}
                harga_bahan_matched = {k: match_price(k, harga_dasar_final) for k in koef_bahan.keys()}
                harga_alat_matched = {k: match_price(k, harga_dasar_final) for k in koef_alat.keys()}

                # Hitung RAB menggunakan engine
                hasil_hitung = sda_engine.hitung_rab_lengkap(
                    volume=volume_input,
                    koef_tenaga=koef_tenaga,
                    koef_bahan=koef_bahan,
                    koef_alat=koef_alat,
                    harga_tenaga=harga_tenaga_matched,
                    harga_bahan=harga_bahan_matched,
                    harga_alat=harga_alat_matched,
                    persen_overhead=persen_overhead, # Ambil dari sidebar
                    persen_ppn=persen_ppn # Ambil dari sidebar
                )

                # Tambahkan ke keranjang
                st.session_state.keranjang_rab_sda.append({
                    "kode_ahsp": selected_pekerjaan['kode_ahsp'],
                    "Uraian Pekerjaan": selected_pekerjaan['uraian_pekerjaan'],
                    "Satuan": selected_pekerjaan['satuan'],
                    "Volume": volume_input,
                    "HSP Tenaga": hasil_hitung['biaya']['hsp_tenaga'],
                    "HSP Bahan": hasil_hitung['biaya']['hsp_bahan'],
                    "HSP Alat": hasil_hitung['biaya']['hsp_alat'],
                    "HSP Sub Total Langsung": hasil_hitung['biaya']['hsp_sub_langsung'],
                    "HSP OHP": hasil_hitung['biaya']['hsp_overhead'],
                    "HSP Tanpa PPN": hasil_hitung['biaya']['hsp_tanpa_ppn'],
                    "Total Tenaga": hasil_hitung['biaya']['total_tenaga_item'],
                    "Total Bahan": hasil_hitung['biaya']['total_bahan_item'],
                    "Total Alat": hasil_hitung['biaya']['total_alat_item'],
                    "Total Sub Total Langsung": hasil_hitung['biaya']['total_sub_langsung_item'],
                    "Total OHP": hasil_hitung['biaya']['total_overhead_item'],
                    "Total Tanpa PPN": hasil_hitung['biaya']['total_tanpa_ppn_item'],
                    "PPN (%)": persen_ppn, # Simpan persen PPN untuk summary
                    "Total PPN": hasil_hitung['biaya']['total_ppn_item'],
                    "Total Dengan PPN": hasil_hitung['biaya']['total_dengan_ppn_item'],
                })
                st.success(f"'{selected_pekerjaan['uraian_pekerjaan']}' dengan volume {volume_input} ditambahkan ke RAB!")
            else:
                st.warning("Volume pekerjaan harus lebih dari 0.")

    st.markdown("---")
    st.subheader("Ringkasan RAB Proyek")

    if st.session_state.keranjang_rab_sda:
        df_rab = pd.DataFrame(st.session_state.keranjang_rab_sda)

        # Tampilkan DataFrame dengan formatting
        st.dataframe(
            df_rab.style.format({
                "Volume": "{:,.2f}",
                "HSP Tenaga": "Rp {:,.2f}",
                "HSP Bahan": "Rp {:,.2f}",
                "HSP Alat": "Rp {:,.2f}",
                "HSP Sub Total Langsung": "Rp {:,.2f}",
                "HSP OHP": "Rp {:,.2f}",
                "HSP Tanpa PPN": "Rp {:,.2f}",
                "Total Tenaga": "Rp {:,.2f}",
                "Total Bahan": "Rp {:,.2f}",
                "Total Alat": "Rp {:,.2f}",
                "Total Sub Total Langsung": "Rp {:,.2f}",
                "Total OHP": "Rp {:,.2f}",
                "Total Tanpa PPN": "Rp {:,.2f}",
                "PPN (%)": "{:,.2f}%",
                "Total PPN": "Rp {:,.2f}",
                "Total Dengan PPN": "Rp {:,.2f}",
            }),
            hide_index=True,
            use_container_width=True
        )

        # Hitung Total Akhir
        grand_total_tanpa_ppn = df_rab['Total Tanpa PPN'].sum()
        grand_total_ppn = df_rab['Total PPN'].sum()
        grand_total_dengan_ppn = df_rab['Total Dengan PPN'].sum()

        st.markdown(
            f"""
            <div style="
                border: 2px solid #0056b3;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                background-color: #e0f2f7;
                box-shadow: 3px 3px 8px rgba(0,0,0,0.2);
            ">
                <h3 style="color:#0056b3;">Rekapitulasi Total RAB</h3>
                <p>Total Biaya (Tanpa PPN): <b>Rp {grand_total_tanpa_ppn:,.2f}</b></p>
                <p>Total PPN ({persen_ppn}%): <b>Rp {grand_total_ppn:,.2f}</b></p>
                <p>GRAND TOTAL (Dengan PPN): <b>Rp {grand_total_dengan_ppn:,.2f}</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_clear, col_export = st.columns([1, 1])
        with col_clear:
            if st.button("Bersihkan RAB"):
                st.session_state.keranjang_rab_sda = []
                st.success("Keranjang RAB telah dibersihkan!")
                st.rerun()
        with col_export:
            # Menggunakan fungsi export_to_excel dari sda_engine
            excel_bytes = sda_engine.export_to_excel(df_rab, nama_proyek=proyek_name)
            st.download_button(
                label="Download RAB Excel",
                data=excel_bytes,
                file_name=f"RAB_{proyek_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.info("Keranjang RAB masih kosong. Silakan tambahkan pekerjaan.")
