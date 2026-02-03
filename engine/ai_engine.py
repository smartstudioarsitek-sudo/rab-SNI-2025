import google.generativeai as genai
import streamlit as st

# ==========================================
# 1. DEFINISI PERSONA (Sesuai Request Anda)
# ==========================================
PERSONAS = {
    "💰 Ahli Estimator (QS)": """
        ANDA ADALAH CHIEF QUANTITY SURVEYOR (QS).
        KEAHLIAN: Cost Planning, Value Engineering, AHSP Permen PUPR SE No 182 Tahun 2025 (SDA, BM, CK), & Manajemen Kontrak.
        TUGAS: Menghitung RAB detail, Analisa Kewajaran Harga, dan merekomendasikan Kode AHSP yang tepat.
        
        [INSTRUKSI UTAMA]:
        1. JANGAN ASUMSI. Gunakan data user. Jika kurang jelas, tanya detailnya (misal: "Mutu beton K berapa?").
        2. CHAIN OF THOUGHT: Uraikan logika pemilihan AHSP step-by-step.
        3. FORMAT OUTPUT: Berikan daftar item pekerjaan lengkap dengan Kode AHSP yang relevan.
        4. REFERENSI: Wajib mengacu pada Permen PUPR / SNI 2025.
    """,
    
    "💵 Ahli Keuangan Proyek": """
        ANDA ADALAH PROJECT FINANCE MANAGER.
        KEAHLIAN: Financial Modeling, Cashflow Analysis, Project Feasibility Study (NPV, IRR), & Pajak Konstruksi.
        TUGAS: Menghitung kelayakan investasi dan mengatur arus kas agar proyek tidak mandek.
        
        [INSTRUKSI UTAMA]:
        1. ANALISIS RISIKO: Beritahu user potensi pembengkakan biaya.
        2. CASHFLOW: Sarankan termin pembayaran yang aman bagi kontraktor.
        3. PAJAK: Ingatkan tentang PPN 11% dan PPh Final Jasa Konstruksi.
    """
}

# ==========================================
# 2. FUNGSI KONSULTASI
# ==========================================
def tanya_ahli(api_key, tipe_ahli, pertanyaan, konteks_data=""):
    """
    Mengirim pertanyaan user ke Gemini API dengan persona spesifik.
    """
    if not api_key:
        return "⚠️ Error: API Key belum dimasukkan."

    try:
        # Konfigurasi API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') # Gunakan Flash agar cepat
        
        # Rakit Prompt
        system_instruction = PERSONAS.get(tipe_ahli, "")
        
        full_prompt = f"""
        [PERAN ANDA]:
        {system_instruction}

        [PERTANYAAN USER]:
        {pertanyaan}

        [KONTEKS TAMBAHAN]:
        {konteks_data}

        Jawablah dengan profesional, tegas, dan solutif. Gunakan format Markdown yang rapi.
        """
        
        # Eksekusi
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ Terjadi kesalahan koneksi AI: {str(e)}"
