# Arsitektur Sistem KALTIDE Intelligence

## Alur Data

```
BMKG API (Forecast Cuaca)
        │
Tide Prediction (PUSHIDROSAL / Tide Gauge)
        │
Curah Hujan Observasi (AWS, ARG, Radar)
        │
DEMNAS (Topografi)
        │
Coastline & River Network
        │
Drainase & Landuse
        │
Historical Rob Database
        │
        ▼
┌─────────────────────────┐
│        AI Engine         │
│  - Data Assimilation     │
│  - Hydrodynamic Model    │
│  - Machine Learning      │
│  - Risk Scoring          │
└─────────────────────────┘
        │
        ▼
   PostgreSQL + PostGIS
        │
        ▼
     FastAPI Backend
        │
        ▼
  React + Leaflet Dashboard
```

## Tiga Engine Utama

### 1. Forecast Engine (`backend/app/engines/forecast_engine.py`)

Menghasilkan prediksi parameter meteorologi (hujan, angin, tekanan udara,
gelombang jika tersedia) dan pasang surut untuk 1-7 hari ke depan.

### 2. Flood Simulation Engine (`backend/app/engines/flood_simulation_engine.py`)

Menghitung area yang berpotensi tergenang berdasarkan elevasi DEM, muka air
laut, pasang, hujan, dan drainase. Output: raster tinggi genangan, polygon
genangan, volume genangan, estimasi durasi.

### 3. Intelligence Engine (`backend/app/engines/intelligence_engine.py`)

Memberikan analisis dampak dan narasi siap-pakai, contoh:

> "Kecamatan Anggana berpotensi mengalami genangan 35-60 cm pada pukul
> 03.00-07.00 WITA. Jalan utama menuju Pelabuhan Anggana diperkirakan
> terdampak sehingga diperlukan peningkatan kewaspadaan."

## Pendekatan Bertahap Pemodelan

| Tahap | Durasi | Pendekatan |
|-------|--------|------------|
| 1 | 6-8 minggu | Rule-Based + GIS — indeks rob dari pasang, hujan, elevasi |
| 2 | 2-3 bulan | Hidrodinamika sederhana — DEM + penyebaran genangan + konektivitas hidrologis |
| 3 | Berkelanjutan | Machine Learning (Random Forest, XGBoost, LSTM) untuk mengoreksi/meningkatkan hasil model fisik |

**Prinsip penting:** model AI digunakan untuk **mengoreksi/meningkatkan**
hasil model fisik, **bukan menggantikannya**.

## API Endpoint

| Endpoint | Deskripsi |
|----------|-----------|
| `GET /forecast/cuaca/{stasiun_id}` | Prakiraan cuaca |
| `GET /forecast/pasang/{stasiun_id}` | Prakiraan pasang surut |
| `GET /tide/{stasiun_id}` | Data pasang surut mentah |
| `GET /flood/prediksi/{stasiun_id}` | Prediksi genangan per kecamatan |
| `GET /warning/{stasiun_id}` | Daftar peringatan dini aktif |
| `GET /impact/{stasiun_id}` | Analisis dampak infrastruktur |
| `GET /stations/` | Daftar stasiun observasi |
| `GET /analytics/ringkasan` | Ringkasan status rob untuk dashboard |

## Skema Database

Lihat `database/schema.sql`. Tabel utama:

`users`, `stations`, `tides`, `forecast`, `rainfall`, `wind`, `dem_tiles`,
`landuse`, `rivers`, `roads`, `villages`, `infrastructure`,
`flood_prediction`, `historical_events`, `warning_logs`.

## Wilayah MVP

- Balikpapan
- Penajam Paser Utara (termasuk kawasan IKN)
- Kutai Kartanegara (Muara Jawa–Anggana)

## Klasifikasi Peringatan Dini

| Status | Emoji | Arti |
|--------|-------|------|
| Aman | 🟢 | Tidak ada potensi genangan signifikan |
| Waspada | 🟡 | Potensi genangan ringan |
| Siaga | 🟠 | Potensi genangan cukup signifikan |
| Awas | 🔴 | Potensi genangan tinggi, membahayakan |

Notifikasi dapat dikirim melalui: WhatsApp Gateway, Telegram Bot, Email,
Web Push Notification.
