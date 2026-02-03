import google.generativeai as genai
import streamlit as st

# ==========================================
# 1. DEFINISI PERSONA (SESUAI REQUEST ANDA)
# ==========================================
PERSONAS = {
    "💰 Ahli Estimator (QS)": """
        ANDA ADALAH CHIEF QUANTITY SURVEYOR (QS).
        KEAHLIAN: Cost Planning, Value Engineering, AHSP Permen PUPR SE NO 30 DAN No 182 Tahun 2025 (SDA, BM, CK, Perumahan), & Manajemen Kontrak.
        TUGAS: Menghitung RAB detail, Bill of Quantities (BoQ), Analisa Kewajaran Harga, dan Pengendalian Biaya Proyek.
        
        [INSTRUKSI WAJIB]:
        1. JANGAN ASUMSI. Gunakan hanya data yang diberikan user. Jika kurang, tanya user detailnya (misal: "Mutu beton berapa? Lokasi dimana?").
        2. CHAIN OF THOUGHT: Sebelum menjawab, uraikan logika analisis Anda step-by-step.
        3. SELF-CORRECTION: Cek ulang hasil perhitungan atau rekomendasi sebelum menampilkannya.
        4. REFERENSI: Selalu mengacu pada standar SNI/PUPR terbaru.
    """,
    
    "💵 Ahli Keuangan Proyek": """
        ANDA ADALAH PROJECT FINANCE MANAGER.
        KEAHLIAN: Financial Modeling, Cashflow Analysis, Project Feasibility Study (NPV, IRR), & Pajak Konstruksi.
        TUGAS: Menghitung kelayakan investasi proyek dan mengatur arus kas agar proyek tidak mandek.
        
        [INSTRUKSI WAJIB]:
        1. JANGAN ASUMSI. Gunakan hanya data yang diberikan user. Jika kurang, tanya user.
        2. CHAIN OF THOUGHT: Sebelum menjawab, uraikan logika analisis Anda step-by-step.
        3. SELF-CORRECTION: Cek ulang hasil perhitungan Anda sebelum menampilkannya.
        4. RISIKO: Selalu ingatkan user tentang risiko cashflow negatif di awal proyek.
    """
}

# ==========================================
# 2. FUNGSI PEMANGGIL GEMINI 1.5 FLASH
# ==========================================
def tanya_ahli(api_key, tipe_ahli, pertanyaan):
    """
    Mengirim prompt ke Google Gemini 1.5 Flash
    """
    if not api_key:
        return "⚠️ Mohon masukkan Google Gemini API Key terlebih dahulu."

    try:
        # Konfigurasi API
        genai.configure(api_key=api_key)
        
        # INI KUNCI KECEPATANNYA: MODEL FLASH ⚡
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        # Ambil instruksi persona
        peran = PERSONAS.get(tipe_ahli, "Anda adalah asisten konstruksi.")
        
        # Rakit Prompt Lengkap
        full_prompt = f"""
        SYSTEM INSTRUCTION:
        {peran}

        USER QUESTION:
        {pertanyaan}

        Jawablah dalam Bahasa Indonesia yang profesional, tegas, dan menggunakan format Markdown (tabel/bullet points) agar mudah dibaca.
        """
        
        # Generate Jawaban
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        return f"🚨 Terjadi Kesalahan: {str(e)}\n\nCek apakah API Key Anda benar atau kuota API habis."
