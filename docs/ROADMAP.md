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
- [x] **Tide Harmonic Engine** — model pasang surut berbasis superposisi konstituen (M2, S2, K1, O1, dst), menggantikan simulasi sinus sederhana. Amplitudo & fase masih **placeholder**, siap dikalibrasi via `scripts/analisis_harmonik_pasang.py` begitu ada data observasi nyata (lihat `docs/PEMODELAN_PASANG_SURUT.md`)
- [x] Flood Simulation Engine (Rule-Based + GIS, Tahap 1)
- [x] Intelligence Engine (narasi & analisis dampak dasar)
- [x] Endpoint REST dasar: forecast, tide, flood, warning, impact, stations, analytics
- [x] Seed data referensi wilayah & stasiun MVP (`database/seed_mvp.sql`) — **placeholder, perlu verifikasi**
- [ ] **Verifikasi & ganti koordinat placeholder di `seed_mvp.sql` dengan data resmi BMKG/PUSHIDROSAL**
- [ ] **Kumpulkan data observasi pasang surut per stasiun (min. 15-29 hari, per-jam)** untuk kalibrasi Tide Harmonic Engine
- [ ] Integrasi nyata ke API BMKG (ganti placeholder di `klien_bmkg.py`)
- [ ] Integrasi nyata ke sumber data pasang surut (PUSHIDROSAL/tide gauge)
- [ ] Ingest data DEMNAS, landuse, sungai, jalan, desa (PostGIS)
- [ ] Dashboard React + Leaflet (peta interaktif, time slider, layer toggle)
- [x] **Analisis dampak berbasis query spasial PostGIS** (`IntelligenceEngine.hitung_dampak_spasial`) — endpoint `/impact` sudah tersambung ke database, TAPI hasilnya 0 sampai tabel `infrastructure`/`roads` diisi data nyata
- [ ] **Isi data infrastruktur nyata** (sekolah/puskesmas/pelabuhan/jalan) lewat Overpass Turbo — lihat `docs/SUMBER_DATA_INFRASTRUKTUR.md`, lalu jalankan `scripts/muat_data_osm.py`
- [ ] Analisis dampak berbasis query spasial nyata (irisan polygon genangan vs infrastruktur) — saat ini masih pakai buffer radius sederhana sambil menunggu polygon genangan Tahap 2
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
