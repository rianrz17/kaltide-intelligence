# Roadmap Pengembangan KALTIDE Intelligence

## Fase Pengembangan

| Fase | Durasi | Target |
|------|--------|--------|
| Fase 1 | 2 bulan | Dashboard GIS + integrasi data BMKG dan pasang surut |
| Fase 2 | 2 bulan | Engine prediksi rob dan peta genangan |
| Fase 3 | 2 bulan | Analisis dampak, notifikasi, dan API publik |
| Fase 4 | 3 bulan | Validasi model, kalibrasi, dan AI untuk peningkatan akurasi |

## Status Saat Ini

- [x] Struktur repo & skeleton backend (FastAPI)
- [x] Skema database PostgreSQL + PostGIS
- [x] Forecast Engine (data dummy, siap disambungkan ke API BMKG asli)
- [x] Flood Simulation Engine (Rule-Based + GIS, Tahap 1)
- [x] Intelligence Engine (narasi & analisis dampak dasar)
- [x] Endpoint REST dasar: forecast, tide, flood, warning, impact, stations, analytics
- [ ] Integrasi nyata ke API BMKG (ganti placeholder di `klien_bmkg.py`)
- [ ] Integrasi nyata ke sumber data pasang surut (PUSHIDROSAL/tide gauge)
- [ ] Ingest data DEMNAS, landuse, sungai, jalan, desa (PostGIS)
- [ ] Dashboard React + Leaflet (peta interaktif, time slider, layer toggle)
- [ ] Analisis dampak berbasis query spasial nyata (irisan polygon genangan vs infrastruktur)
- [ ] Sistem notifikasi (WhatsApp Gateway, Telegram Bot, Email, Web Push)
- [ ] Model hidrodinamika sederhana (Tahap 2)
- [ ] Model Machine Learning koreksi (Tahap 3): Random Forest, XGBoost, LSTM
- [ ] Validasi lapangan & kalibrasi dengan data historis rob

## Wilayah MVP

1. **Balikpapan**
2. **Penajam Paser Utara** (termasuk kawasan IKN)
3. **Kutai Kartanegara** (Muara Jawa–Anggana)

Wilayah ini dipilih karena risiko rob relatif tinggi, tersedia data
pendukung, dan cocok untuk validasi model sebelum diperluas ke seluruh
pesisir Kalimantan Timur.

## Arah Jangka Panjang

Setelah MVP stabil:

- Kembangkan menjadi **Decision Support System (DSS)** untuk BMKG, BPBD,
  pemerintah daerah, operator pelabuhan, dan pengelola kawasan pesisir.
- Selaraskan arsitektur & desain antarmuka dengan platform SiCASMA agar
  memiliki ekosistem yang konsisten.
- Standar operasional mendekati sistem BMKG, berpotensi menjadi platform
  layanan nasional untuk informasi banjir rob — dengan referensi desain
  dari NOAA Coastal Flood Forecast System dan layanan prediksi banjir
  pesisir Deltares, disesuaikan dengan karakteristik pesisir tropis
  Indonesia.

## Catatan Teknis untuk Tim

- Model AI/ML **mengoreksi**, bukan **menggantikan**, model fisik.
- Semua perubahan skema database harus didokumentasikan sebagai file
  migrasi baru di `database/migrations/`.
- Endpoint baru harus didaftarkan di `backend/app/main.py` dan
  didokumentasikan di `docs/ARSITEKTUR.md`.
