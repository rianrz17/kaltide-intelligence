# KALTIDE Intelligence

**Kalimantan Tidal Flood Intelligence System**

> "Predicting Coastal Flood Risk with Weather, Tide, and Geospatial Intelligence."

Platform geospasial cerdas yang mengintegrasikan data meteorologi, oseanografi, dan
topografi untuk memprediksi potensi banjir rob (pasang laut) di pesisir Kalimantan
Timur secara spasial dan temporal.

Output yang dihasilkan bukan sekadar "akan terjadi rob", melainkan:

- lokasi genangan
- tinggi genangan
- waktu mulai & waktu puncak
- durasi genangan
- tingkat risiko
- dampak terhadap infrastruktur (jalan, sekolah, puskesmas, pelabuhan, permukiman)

## Cakupan MVP

Fase awal (MVP) difokuskan pada 3 wilayah prioritas dengan risiko rob tinggi:

- Balikpapan
- Penajam Paser Utara (termasuk kawasan IKN)
- Kutai Kartanegara (Muara Jawa–Anggana)

## Status Pengembangan

Repo ini sedang berada di **Tahap 1: Rule-Based + GIS** (lihat `docs/ROADMAP.md`).

## Struktur Repo

```
kaltide-intelligence/
├── backend/          # FastAPI backend (API, engine prediksi, koneksi database)
│   └── app/
│       ├── api/       # Endpoint REST (forecast, tide, flood, warning, dll)
│       ├── core/      # Konfigurasi & koneksi database
│       ├── models/    # Skema data (Pydantic)
│       ├── engines/   # Forecast Engine, Flood Simulation Engine, Intelligence Engine
│       └── services/  # Klien eksternal (BMKG, PUSHIDROSAL, dll)
├── frontend/          # Dashboard React + Leaflet
├── database/          # Skema PostgreSQL + PostGIS & migrasi
├── data/              # Data mentah & olahan (DEM, curah hujan, pasang surut)
├── scripts/           # Script ingestion data & utilitas
├── notebooks/         # Eksplorasi data & prototipe model (Jupyter)
└── docs/              # Dokumentasi arsitektur & roadmap
```

## Cara Menjalankan (Development)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env   # sesuaikan isinya
uvicorn app.main:app --reload
```

Backend akan berjalan di `http://localhost:8000` dengan dokumentasi otomatis di
`http://localhost:8000/docs`.

### 2. Database

```bash
docker compose up -d db
psql -h localhost -U kaltide -d kaltide -f database/schema.sql
```

### 3. Seluruh stack (Docker Compose)

```bash
docker compose up -d
```

## Teknologi

| Komponen         | Teknologi                          |
|------------------|-------------------------------------|
| Backend API      | FastAPI (Python)                   |
| Database         | PostgreSQL + PostGIS               |
| Frontend         | React + Leaflet                    |
| Model Tahap 1    | Rule-Based + analisis GIS          |
| Model Tahap 2    | Hidrodinamika sederhana (DEM-based)|
| Model Tahap 3    | Machine Learning (RF, XGBoost, LSTM)|

## Roadmap

Lihat `docs/ROADMAP.md` untuk rincian fase dan target pengembangan.

## Lisensi

Belum ditentukan (TBD) — sesuaikan dengan kebijakan instansi/tim sebelum rilis publik.
