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

==========================================
# 2. FUNGSI PEMANGGIL AI (DYNAMIC MODEL) 🧠
# ==========================================
def tanya_ahli(api_key, tipe_ahli, pertanyaan, model_name="gemini-2.0-flash"):
    """
    Mengirim prompt ke Google Gemini dengan Model yang DIPILIH USER.
    """
    if not api_key:
        return "⚠️ Mohon masukkan Google Gemini API Key terlebih dahulu."

    try:
        # Konfigurasi API
        genai.configure(api_key=api_key)
        
        # --- GUNAKAN MODEL SESUAI PILIHAN USER ---
        # Parameter 'model_name' dikirim dari halaman depan (UI)
        model = genai.GenerativeModel(model_name) 
        
        # Ambil instruksi persona
        peran = PERSONAS.get(tipe_ahli, "Anda adalah asisten konstruksi.")
        
        # Rakit Prompt
        full_prompt = f"""
        PERAN SYSTEM:
        {peran}

        PERTANYAAN USER:
        {pertanyaan}

        INSTRUKSI:
        Jawablah dalam Bahasa Indonesia yang profesional. Gunakan Markdown (Bold, Tabel, List).
        """
        
        # Generate Jawaban
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return f"""
            🚨 **KUOTA HABIS (Limit Tercapai)**
            
            Model `{model_name}` sedang sibuk atau limit harian Anda habis.
            👉 **SOLUSI:** Silakan ganti **Model AI** di Sidebar (misal: coba pilih 'Gemini Pro' atau 'Flash 1.5').
            """
        elif "404" in error_msg:
             return f"""
            🚨 **MODEL TIDAK DITEMUKAN**
            
            Model `{model_name}` tidak tersedia untuk API Key ini.
            👉 **SOLUSI:** Pilih model lain di Sidebar yang lebih umum (misal: 'Gemini Pro').
            """
        else:
            return f"🚨 **Terjadi Kesalahan:** {error_msg}"
