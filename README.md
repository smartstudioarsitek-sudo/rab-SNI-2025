# Aplikasi RAB SDA 2025

Aplikasi Rencana Anggaran Biaya (RAB) berbasis AHSP SDA 2025
Dibangun menggunakan Python dan Streamlit dengan pendekatan deterministik dan audit-safe.

Aplikasi ini dirancang untuk memudahkan engineer dalam menyusun BOQ dan RAB secara konsisten sesuai standar PU, serta dapat dikembangkan ke bidang lain (Cipta Karya dan Bina Marga).

---

## 🎯 Tujuan

 Menyusun RAB berdasarkan AHSP resmi
 Menghindari kesalahan hitung manual
 Memisahkan data AHSP, engine hitung, dan UI
 Siap dikembangkan untuk skala besar (ribuan AHSP)

---

## 🚧 Ruang Lingkup (Phase 1 – Core)

Saat ini aplikasi mencakup

 Bidang Sumber Daya Air (SDA)
 AHSP SDA 2025 – Pekerjaan Tanah Manual

   Pembersihan & stripping
   Pembabadan rumput
   Galian batu manual
 Perhitungan biaya tenaga kerja
 Multi-item BOQ
 Rekap total RAB

 Catatan Perhitungan bahan dan alat akan ditambahkan pada fase berikutnya.

---

## 🧱 Struktur Project

```
rab-sda-2025
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data
│   └── ahsp_sda_2025_tanah_manual_core.xlsx
│
├── engine
│   ├── __init__.py
│   └── sda_engine.py
│
└── export
    └── excel_export.py
```

---

## ⚙️ Teknologi

 Python 3.10+
 Streamlit
 Pandas
 OpenPyXL

---

## ▶️ Cara Menjalankan Aplikasi

1. Clone repository

```bash
git clone httpsgithub.comUSERNAMErab-sda-2025.git
cd rab-sda-2025
```

2. Install dependency

```bash
pip install -r requirements.txt
```

3. Jalankan aplikasi

```bash
streamlit run app.py
```

---

## 🧮 Cara Pakai Singkat

1. Pilih kode AHSP
2. Masukkan volume pekerjaan
3. Masukkan upah tenaga kerja
4. Klik Tambah ke BOQ
5. Lihat Rekap Total RAB

---

## 🔒 Prinsip Desain

 Perhitungan tidak menggunakan AI
 Koefisien AHSP bersifat normatif
 Database AHSP terpisah dari engine
 Mudah diperluas ke

   Cipta Karya (CK)
   Bina Marga (BM)

---

## 🚀 Rencana Pengembangan

 Export BOQ & RAB ke Excel
 Penambahan biaya bahan dan alat
 Multi-bidang (CK & Bina Marga)
 Narasi laporan otomatis (AI assist)

---

## 📌 Catatan

Aplikasi ini dikembangkan untuk kebutuhan teknis dan pembelajaran.
Pastikan selalu menggunakan AHSP resmi terbaru untuk pekerjaan proyek.

---
