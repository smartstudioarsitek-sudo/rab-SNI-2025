import streamlit as st

# Coba import engine dengan aman
try:
    from engine import ai_engine
except ImportError:
    st.error("🚨 Gagal memuat 'engine/ai_engine.py'. Pastikan file tersebut ada dan tidak ada error syntax.")
    st.stop()
except SyntaxError:
    st.error("🚨 Terjadi SyntaxError di 'engine/ai_engine.py'. Cek kembali kodingannya.")
    st.stop()

# ==========================================
# CONFIG HALAMAN
# ==========================================
st.set_page_config(page_title="Konsultan AI", page_icon="🤖", layout="wide")
st.title("🤖 AI Construction Consultant")

# ==========================================
# 1. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🔑 Konfigurasi")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    st.subheader("🧠 Pilih Otak AI")
    # Mapping Nama Keren -> Kode Teknis
    pilihan_model = {
        "⚡ Gemini 2.0 Flash (Cepat)": "gemini-2.0-flash",
        "🚀 Gemini 1.5 Flash (Stabil)": "gemini-1.5-flash",
        "🧠 Gemini 1.5 Pro (Pintar)": "gemini-1.5-pro",
        "🛡️ Gemini Pro (Legacy)": "gemini-pro"
    }
    
    label_model = st.selectbox("Model:", list(pilihan_model.keys()), index=0)
    kode_model = pilihan_model[label_model]
    
    st.caption(f"Active Model: `{kode_model}`")

# ==========================================
# 2. AREA CHAT
# ==========================================
col_pakar, col_chat = st.columns([1, 2])

with col_pakar:
    st.success("👨‍💼 **Pilih Pakar:**")
    tipe_ahli = st.radio("Konsultan:", ["💰 Ahli Estimator (QS)", "💵 Ahli Keuangan Proyek"])

with col_chat:
    st.subheader("💬 Ruang Diskusi")
    user_query = st.text_area("Pertanyaan:", height=150)
    
    if st.button("🚀 Kirim Pertanyaan", type="primary"):
        if not api_key:
            st.warning("⚠️ Masukkan API Key di Sidebar.")
        elif not user_query:
            st.warning("⚠️ Pertanyaan kosong.")
        else:
            with st.spinner("Sedang menganalisis..."):
                jawaban = ai_engine.tanya_ahli(
                    api_key=api_key,
                    tipe_ahli=tipe_ahli,
                    pertanyaan=user_query,
                    model_name=kode_model
                )
                st.markdown("---")
                st.markdown(jawaban)
