import streamlit as st
import google.generativeai as genai
import importlib.metadata

st.set_page_config(page_title="API Debugger", page_icon="🛠️")

st.title("🛠️ Gemini API Inspector")
st.caption("Cek versi library dan model yang tersedia untuk API Key Anda.")

# 1. CEK VERSI LIBRARY PYTHON
try:
    version = importlib.metadata.version("google-generativeai")
    st.info(f"📦 Versi Library `google-generativeai` saat ini: **{version}**")
    
    # Analisis Versi
    major, minor, patch = map(int, version.split('.')[:3])
    if minor < 4: # Versi lama
        st.error("🚨 Versi Library Terlalu Lama! `gemini-1.5-flash` butuh minimal versi 0.5.0 atau 0.7.0")
        st.markdown("👉 **Solusi:** Update `requirements.txt` Anda menjadi: `google-generativeai>=0.7.0`")
    else:
        st.success("✅ Versi Library sudah mendukung Model Terbaru.")
        
except Exception as e:
    st.warning(f"Tidak bisa mendeteksi versi library: {e}")

st.divider()

# 2. CEK KETERSEDIAAN MODEL
api_key = st.text_input("Masukkan API Key Anda:", type="password")

if st.button("🔍 Scan Model Tersedia"):
    if not api_key:
        st.error("Masukkan API Key dulu bos!")
    else:
        try:
            genai.configure(api_key=api_key)
            
            st.write("Sedang menghubungi server Google...")
            models = list(genai.list_models())
            
            found_flash = False
            available_models = []

            for m in models:
                # Kita hanya cari model yang bisa generate text (generateContent)
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
                    if 'gemini-1.5-flash' in m.name:
                        found_flash = True

            # Tampilkan Hasil
            st.write("### 📋 Daftar Model yang Diizinkan:")
            st.json(available_models)
            
            st.divider()
            if found_flash:
                st.success("✅ **KABAR BAIK:** Akun Anda memiliki akses ke `models/gemini-1.5-flash`!")
                st.info("Jika masih error, pastikan penulisan di kode `ai_engine.py` adalah `gemini-1.5-flash` (tanpa 'models/' di depan jika pakai library terbaru, atau sesuaikan).")
            else:
                st.error("❌ **MASALAH DITEMUKAN:** Model `gemini-1.5-flash` TIDAK MUNCUL di daftar.")
                st.markdown("""
                **Kemungkinan Penyebab:**
                1. Versi Library Streamlit Cloud lama (paling sering).
                2. API Key Anda tipe lama/terbatas.
                
                **Saran:** Gunakan model `gemini-pro` saja di `ai_engine.py` karena model itu pasti ada di daftar di atas.
                """)
                
        except Exception as e:
            st.error(f"🚨 Koneksi Gagal: {e}")
