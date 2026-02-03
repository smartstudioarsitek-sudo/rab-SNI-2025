import streamlit as st
import pandas as pd

# Import Engine AI yang baru dibuat
try:
    from engine import ai_engine
except ImportError:
    st.error("🚨 File engine/ai_engine.py tidak ditemukan!")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Konsultan AI", page_icon="🤖", layout="wide")
st.title("🤖 Konsultan Tenaga Ahli (AI)")
st.caption("Diskusi teknis dengan AI Estimator & Finance Manager (Powered by Gemini)")

# ==========================================
# 1. SETUP API KEY
# ==========================================
with st.sidebar:
    st.header("🔑 Kunci Akses")
    # Disarankan simpan di st.secrets, tapi untuk demo bisa input manual
    api_key = st.text_input("Masukkan Google Gemini API Key:", type="password")
    st.caption("Dapatkan Key gratis di: [Google AI Studio](https://aistudio.google.com/)")
    
    st.divider()
    st.info("💡 **Tips:** Tanyakan hal seperti 'Apa saja item pekerjaan untuk membuat saluran irigasi panjang 100m?'")

# ==========================================
# 2. PILIH TENAGA AHLI
# ==========================================
col_ahli, col_chat = st.columns([1, 2])

with col_ahli:
    st.subheader("👨‍💼 Pilih Konsultan")
    tipe_ahli = st.radio(
        "Siapa yang ingin Anda tanya?",
        ["💰 Ahli Estimator (RAB)", "💵 Ahli Keuangan Proyek"]
    )
    
    # Tampilkan Deskripsi Singkat
    if "Estimator" in tipe_ahli:
        st.success("Spesialis: AHSP 2025, Volume, & Teknis Sipil.")
    else:
        st.info("Spesialis: Cashflow, Profit, & Risiko Keuangan.")

# ==========================================
# 3. INTERFACE CHAT
# ==========================================
with col_chat:
    st.subheader("💬 Ruang Diskusi")
    
    # Input Pertanyaan
    user_query = st.text_area("Jelaskan kebutuhan proyek Anda:", height=150, 
        placeholder="Contoh: Saya mau bangun jalan beton K-300 lebar 4m tebal 20cm sepanjang 1km. Tolong list item pekerjaan dan kode AHSP Bina Marga yang harus saya pakai.")
    
    # Tombol Eksekusi
    if st.button("🚀 Tanya Ahli Sekarang", type="primary"):
        if not api_key:
            st.error("⚠️ Harap masukkan API Key di Sidebar terlebih dahulu!")
        elif not user_query:
            st.warning("⚠️ Pertanyaan tidak boleh kosong.")
        else:
            with st.spinner(f"{tipe_ahli} sedang menganalisis Permen PUPR..."):
                # Panggil Fungsi AI
                jawaban = ai_engine.tanya_ahli(api_key, tipe_ahli, user_query)
                
                # Tampilkan Jawaban
                st.markdown("---")
                st.markdown(f"### 📝 Jawaban {tipe_ahli}")
                st.markdown(jawaban)
                
                # Fitur Tambahan: Copy Prompt (Opsional)
                st.caption("✅ Analisis selesai. Silakan input item di atas ke menu kalkulator.")

# ==========================================
# 4. CONTOH KASUS (Prompt Engineering)
# ==========================================
st.divider()
with st.expander("📚 Contoh Pertanyaan yang Bagus"):
    st.markdown("""
    **Untuk Estimator (RAB):**
    * "Saya mau buat Dinding Penahan Tanah (DPT) batu kali tinggi 3 meter. Item pekerjaannya apa saja menurut AHSP SDA?"
    * "Berapa koefisien tenaga kerja untuk beton K-250 manual vs ready mix? Mana yang lebih efisien?"
    
    **Untuk Keuangan Proyek:**
    * "Proyek senilai 1M, termin pembayaran 30% - 30% - 40%. Bagaimana proyeksi cashflow agar saya tidak rugi di bulan ke-2?"
    * "Berapa estimasi pajak yang harus saya sisihkan untuk proyek pemerintah?"
    """)
