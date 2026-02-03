import streamlit as st

# Import Engine AI
try:
    from engine import ai_engine
except ImportError:
    st.error("🚨 File engine/ai_engine.py tidak ditemukan!")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Konsultan AI", page_icon="🤖", layout="wide")
st.title("🤖 AI Construction Consultant")
st.caption("Diskusi Real-time dengan Tenaga Ahli Digital")

# ==========================================
# 1. SIDEBAR: KONFIGURASI OTAK ⚙️
# ==========================================
with st.sidebar:
    st.header("🔑 Kunci & Konfigurasi")
    
    # Input API Key
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    # --- PILIH MODEL (FITUR BARU) ---
    st.subheader("🧠 Pilih Otak AI")
    st.info("Jika error 'Quota Exceeded' (429) atau 'Not Found' (404), ganti model di bawah ini:")
    
    # Daftar Model (Label : Kode Teknis)
    pilihan_model = {
        "⚡ Gemini 2.0 Flash (Terbaru & Cepat)": "gemini-2.0-flash",
        "🚀 Gemini 1.5 Flash (Stabil & Ringan)": "gemini-1.5-flash",
        "🧠 Gemini 1.5 Pro (Lebih Pintar)": "gemini-1.5-pro",
        "🛡️ Gemini Pro (Versi Lama/Cadangan)": "gemini-pro"
    }
    
    label_model = st.selectbox("Model:", list(pilihan_model.keys()), index=0)
    kode_model_terpilih = pilihan_model[label_model] # Ini yang dikirim ke engine
    
    st.caption(f"Menggunakan: `{kode_model_terpilih}`")

# ==========================================
# 2. AREA UTAMA
# ==========================================
col_pakar, col_chat = st.columns([1, 2])

with col_pakar:
    st.success("👨‍💼 **Pilih Tenaga Ahli:**")
    tipe_ahli = st.radio(
        "Siapa lawan bicara Anda?",
        ["💰 Ahli Estimator (QS)", "💵 Ahli Keuangan Proyek"]
    )
    
    st.markdown("---")
    st.markdown("""
    **Cara Mengatasi Error:**
    1. Jika muncul **Error 429**, berarti kuota model tersebut habis. Ganti ke model lain di sidebar.
    2. Jika muncul **Error 404**, berarti library belum support model baru. Pilih 'Gemini Pro'.
    """)

with col_chat:
    st.subheader(f"💬 Ruang Diskusi ({tipe_ahli})")
    
    user_query = st.text_area("Tulis pertanyaan proyek Anda:", height=150)
    
    if st.button("🚀 Analisis Sekarang", type="primary"):
        if not api_key:
            st.warning("⚠️ Masukkan API Key dulu di Sidebar.")
        elif not user_query:
            st.warning("⚠️ Pertanyaan kosong.")
        else:
            with st.spinner(f"Sedang berpikir menggunakan {kode_model_terpilih}..."):
                
                # --- PANGGIL FUNGSI DENGAN MODEL DINAMIS ---
                jawaban = ai_engine.tanya_ahli(
                    api_key=api_key, 
                    tipe_ahli=tipe_ahli, 
                    pertanyaan=user_query,
                    model_name=kode_model_terpilih  # <--- INI KUNCINYA
                )
                
                st.markdown("---")
                st.markdown(jawaban)
