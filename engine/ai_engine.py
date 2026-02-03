import google.generativeai as genai
import streamlit as st

# ==========================================
# 1. DEFINISI PERSONA
# ==========================================
PERSONAS = {
    "💰 Ahli Estimator (QS)": """
        ANDA ADALAH CHIEF QUANTITY SURVEYOR (QS) SENIOR.
        KEAHLIAN: Cost Planning, Analisa Harga Satuan (AHSP 2025), & Manajemen Kontrak Konstruksi.
        TUGAS: Menerjemahkan kebutuhan teknis user menjadi ITEM PEKERJAAN dan KODE AHSP yang relevan.
        GAYA BAHASA: Profesional, to-the-point, dan solutif.
    """,
    "💵 Ahli Keuangan Proyek": """
        ANDA ADALAH PROJECT FINANCE MANAGER.
        KEAHLIAN: Cashflow, Pajak (PPN 11%, PPh Final), & Analisa Risiko.
        TUGAS: Memberikan strategi keuangan agar kontraktor tidak boncos.
    """
}

# ==========================================
# 2. FUNGSI PEMANGGIL AI
# ==========================================
def tanya_ahli(api_key, tipe_ahli, pertanyaan, model_name="gemini-2.0-flash"):
    if not api_key:
        return "⚠️ Mohon masukkan Google Gemini API Key terlebih dahulu."

    try:
        genai.configure(api_key=api_key)
        
        # Gunakan model sesuai pilihan user
        model = genai.GenerativeModel(model_name)
        
        peran = PERSONAS.get(tipe_ahli, "Anda adalah asisten konstruksi.")
        
        full_prompt = f"""
        PERAN SYSTEM:
        {peran}

        PERTANYAAN USER:
        {pertanyaan}

        INSTRUKSI:
        Jawablah dalam Bahasa Indonesia yang profesional. Gunakan Markdown.
        """
        
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        # Handle Error dengan Rapi
        if "429" in error_msg:
            return f"🚨 **KUOTA HABIS:** Model `{model_name}` sedang limit. Silakan ganti model lain di Sidebar."
        elif "404" in error_msg:
            return f"🚨 **MODEL TIDAK DITEMUKAN:** Model `{model_name}` tidak support. Pilih 'Gemini Pro' di Sidebar."
        else:
            return f"🚨 **Terjadi Kesalahan:** {error_msg}"
