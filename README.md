---
title: Competitor Radar
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.29.1
python_version: '3.12'
app_file: run_app.py
pinned: false
license: mit
---

# 📡 CompetitorRadar AI — Sistem Riset Kompetitor Aplikasi Android

Sistem intelijen pasar (*Competitor Intelligence*) berbasis AI untuk menganalisis aplikasi Android kompetitor, mengekstrak inovasi fitur yang belum diadopsi, mengaudit titik friksi *user flow*, dan menyajikan laporan komprehensif beserta bukti sitasi sumber resmi (*provenance links*).

---

## 🌟 Fitur Utama

1. **Formulir Modular Aplikasi Internal (Baseline Riset)**:
   - Input detail aplikasi Anda: Profil umum, target audiens, hierarki modul & fitur.
   - Perekaman langkah demi langkah alur pengguna (*user flow*).
   - Fitur **Export & Import JSON** agar profil dapat disimpan dan digunakan berulang kali untuk berbagai sesi riset.
2. **Pengumpulan Data Multi-Sumber Otomatis**:
   - **Google Play Store Scraper**: Mengambil metadata, skor rating, volume unduhan, changelog rilis terbaru, serta ratusan ulasan pengguna (dipilah otomatis menjadi *Praises* dan *Complaints*).
   - **Official Website & External Scraper**: Mengikis halaman resmi perusahaan, deskripsi produk, daftar keunggulan fitur, serta artikel berita eksternal pendukung.
   - Fitur **Live Preview Test** sebelum kompetitor disimpan ke database.
3. **Mesin Analisis AI Multi-Provider**:
   - Mendukung **Google Gemini** (Gemini 2.5 Flash / Pro).
   - Mendukung **Qwen (Alibaba Cloud DashScope)**: `qwen-plus`, `qwen-max`, `qwen-turbo`, atau model kustom lainnya melalui endpoint OpenAI-compatible.
   - Mendukung **OpenAI** (GPT-4o) dan **Anthropic Claude** (Claude 3.5 Sonnet).
   - Konfigurasi API Key dapat diatur langsung melalui antarmuka web tanpa menyentuh kode.
   - Dilengkapi *Intelligent Heuristic Synthesizer* bawaan saat offline atau jika API Key belum disetel.
4. **Matriks Gap Inovasi Fitur Interaktif**:
   - Identifikasi status adopsi: `Belum Diadaptasi (Gap)`, `Sebagian Diadaptasi`, `Sudah Setara`, atau `Aplikasi Kita Lebih Unggul`.
   - Klasifikasi prioritas adaptasi: Skor *Impact (1-10)* vs *Effort (1-10)* serta label otomatis *Quick Win* vs *Strategic Project*.
   - **Sitasi Sumber Resmi**: Tautan langsung (*hyperlink*) ke ulasan Play Store, halaman website resmi kompetitor, atau changelog rilis.
   - Filter pencarian instan dan penyaringan berdasarkan status maupun modul.
5. **Audit Friksi User Flow (Friction & Simplification)**:
   - Komparasi langkah flow aplikasi internal berdampingan (*side-by-side*) dengan pendekatan alur cepat kompetitor.
   - Deteksi titik hambatan (*UX Friction Points*) dan rekomendasi konkret pemangkasan langkah interaksi.
6. **Visual Analytics & Ekspor Multi-Format**:
   - **Radar Chart**: Skor kematangan fungsional per pilar produk.
   - **Impact vs Effort Quadrant**: Panduan visual untuk menentukan roadmap fitur.
   - **Ekspor 1-Klik**: Unduh laporan eksekutif siap cetak (**PDF/HTML**), spreadsheet data (**Excel .xlsx**), tabel mentah (**CSV**), dan dokumentasi tim (**Markdown .md**).

---

## 🚀 Panduan Menjalankan Sistem

### Cara 1: Sekali Klik (Rekomendasi)
Cukup jalankan script batch atau PowerShell di folder root:
- Dobel klik file `run.bat`, atau
- Buka terminal PowerShell dan jalankan:
  ```powershell
  .\run.ps1
  ```
Browser akan otomatis terbuka di `http://localhost:8000`.

---

### Cara 2: Menjalankan Manual via Terminal

#### 1. Menjalankan Backend FastAPI:
```powershell
cd C:\Users\Apip\.gemini\antigravity\scratch\competitor-radar\backend
python -m uvicorn app.main:app --port 8000 --reload
```
Akses dashboard di browser: `http://localhost:8000`.

#### 2. Menjalankan Frontend Development Mode (Opsional):
Jika Anda ingin mengembangkan antarmuka secara aktif dengan Hot-Reloading:
```powershell
cd C:\Users\Apip\.gemini\antigravity\scratch\competitor-radar\frontend
npm run dev
```
Akses antarmuka dev di: `http://localhost:3000`.

---

## 📂 Struktur Direktori Proyek

```text
competitor-radar/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routers/
│   │   │       ├── projects.py       # Manajemen sesi proyek riset
│   │   │       ├── internal_app.py   # Baseline profil internal & import/export JSON
│   │   │       ├── competitors.py    # Kelola kompetitor & live test scraping
│   │   │       ├── analysis.py       # AI gap analysis & retrieval laporan
│   │   │       ├── exports.py        # Ekspor Excel, CSV, Markdown, dan HTML/PDF
│   │   │       └── settings.py       # Pengaturan API Key multi-provider
│   │   ├── core/
│   │   │   ├── config.py             # Konfigurasi aplikasi
│   │   │   └── database.py           # Inisialisasi engine SQLite & SQLModel
│   │   ├── models/
│   │   │   └── models.py             # Skema tabel database relasional
│   │   ├── services/
│   │   │   ├── scraper_playstore.py  # Ekstraksi ulasan, changelog, rating Play Store
│   │   │   ├── scraper_web.py        # Ekstraksi konten website resmi kompetitor
│   │   │   ├── llm_adapter.py        # Adapter Gemini, OpenAI, Claude & fallback
│   │   │   ├── analysis_engine.py    # Orkestrasi analisis & sintesis AI
│   │   │   └── exporter.py           # Generator file Excel, CSV, Markdown, HTML
│   │   └── main.py                   # FastAPI app, static serving, & seed data
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx            # Navigasi, switcher proyek, trigger riset & ekspor
│   │   │   ├── FeatureGapTable.tsx   # Matriks gap fitur interaktif & sitasi resmi
│   │   │   ├── UserFlowComparison.tsx# Analisis friksi alur berdampingan
│   │   │   ├── ChartsSection.tsx     # Visualisasi Radar Chart & Kuadran Prioritas
│   │   │   ├── InternalAppForm.tsx   # Form modular internal app & JSON export/import
│   │   │   ├── CompetitorsManager.tsx# Kelola kompetitor & live scraping preview
│   │   │   ├── SettingsTab.tsx       # Konfigurasi API keys multi-provider
│   │   │   └── NewProjectModal.tsx   # Modal buat proyek riset baru
│   │   ├── App.tsx                   # Dashboard utama
│   │   ├── api.ts                    # REST client komunikasi backend
│   │   └── types.ts                  # Definisi TypeScript
│   ├── package.json
│   └── vite.config.ts
├── run.bat                           # Launcher Windows Batch
├── run.ps1                           # Launcher PowerShell
└── README.md
```
