-- =====================================================================
-- KALTIDE Intelligence - Skema Database
-- PostgreSQL + PostGIS
-- =====================================================================
-- Jalankan setelah database dibuat, contoh:
--   psql -h localhost -U kaltide -d kaltide -f database/schema.sql
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------------------------------------------------------------------
-- Pengguna
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    nama            VARCHAR(150) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    kata_sandi_hash VARCHAR(255) NOT NULL,
    peran           VARCHAR(50) NOT NULL DEFAULT 'viewer', -- admin | operator | viewer
    instansi        VARCHAR(150),                          -- BMKG, BPBD, Pemda, dll
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Stasiun observasi (AWS, ARG, tide gauge, radar)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stations (
    id              VARCHAR(50) PRIMARY KEY,
    nama            VARCHAR(150) NOT NULL,
    jenis           VARCHAR(30) NOT NULL, -- aws | arg | tide_gauge | radar
    kecamatan       VARCHAR(100),
    kabupaten_kota  VARCHAR(100),
    geom            GEOMETRY(Point, 4326) NOT NULL,
    aktif           BOOLEAN NOT NULL DEFAULT true,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stations_geom ON stations USING GIST (geom);

-- ---------------------------------------------------------------------
-- Prakiraan pasang surut
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tides (
    id                   BIGSERIAL PRIMARY KEY,
    station_id           VARCHAR(50) NOT NULL REFERENCES stations(id),
    waktu                TIMESTAMPTZ NOT NULL,
    tinggi_muka_air_m    NUMERIC(6,3) NOT NULL,
    jenis                VARCHAR(20) NOT NULL DEFAULT 'prediksi', -- prediksi | observasi
    dibuat_pada          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (station_id, waktu, jenis)
);
CREATE INDEX IF NOT EXISTS idx_tides_waktu ON tides (waktu);

-- ---------------------------------------------------------------------
-- Prakiraan cuaca (forecast BMKG)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecast (
    id                     BIGSERIAL PRIMARY KEY,
    station_id             VARCHAR(50) NOT NULL REFERENCES stations(id),
    waktu                  TIMESTAMPTZ NOT NULL,
    curah_hujan_mm         NUMERIC(6,2) DEFAULT 0,
    kecepatan_angin_ms     NUMERIC(5,2),
    arah_angin_derajat     NUMERIC(5,2),
    tekanan_udara_hpa      NUMERIC(6,2),
    dibuat_pada            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (station_id, waktu)
);
CREATE INDEX IF NOT EXISTS idx_forecast_waktu ON forecast (waktu);

-- ---------------------------------------------------------------------
-- Observasi curah hujan (AWS/ARG/radar)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rainfall (
    id              BIGSERIAL PRIMARY KEY,
    station_id      VARCHAR(50) NOT NULL REFERENCES stations(id),
    waktu           TIMESTAMPTZ NOT NULL,
    curah_hujan_mm  NUMERIC(6,2) NOT NULL,
    sumber          VARCHAR(20) NOT NULL DEFAULT 'aws', -- aws | arg | radar
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_rainfall_waktu ON rainfall (waktu);

-- ---------------------------------------------------------------------
-- Observasi angin
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wind (
    id                  BIGSERIAL PRIMARY KEY,
    station_id          VARCHAR(50) NOT NULL REFERENCES stations(id),
    waktu               TIMESTAMPTZ NOT NULL,
    kecepatan_ms        NUMERIC(5,2),
    arah_derajat        NUMERIC(5,2),
    dibuat_pada         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Tile/raster DEM (referensi lokasi file, bukan menyimpan raster di DB)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dem_tiles (
    id              SERIAL PRIMARY KEY,
    nama_tile       VARCHAR(150) NOT NULL,
    path_file       VARCHAR(255) NOT NULL, -- lokasi file raster (data/dem/...)
    resolusi_m      NUMERIC(6,2),
    bbox            GEOMETRY(Polygon, 4326) NOT NULL,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dem_tiles_bbox ON dem_tiles USING GIST (bbox);

-- ---------------------------------------------------------------------
-- Landuse (tata guna lahan)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS landuse (
    id              SERIAL PRIMARY KEY,
    kategori        VARCHAR(100) NOT NULL, -- permukiman, tambak, mangrove, dll
    geom            GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_landuse_geom ON landuse USING GIST (geom);

-- ---------------------------------------------------------------------
-- Jaringan sungai
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rivers (
    id              SERIAL PRIMARY KEY,
    nama            VARCHAR(150),
    orde_sungai     INTEGER,
    geom            GEOMETRY(MultiLineString, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rivers_geom ON rivers USING GIST (geom);

-- ---------------------------------------------------------------------
-- Jaringan jalan (untuk analisis dampak)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roads (
    id              SERIAL PRIMARY KEY,
    nama            VARCHAR(150),
    kelas           VARCHAR(50), -- nasional, provinsi, kabupaten
    geom            GEOMETRY(MultiLineString, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_roads_geom ON roads USING GIST (geom);

-- ---------------------------------------------------------------------
-- Batas wilayah administrasi (desa/kelurahan)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS villages (
    id                  SERIAL PRIMARY KEY,
    nama                VARCHAR(150) NOT NULL,
    kecamatan           VARCHAR(100) NOT NULL,
    kabupaten_kota      VARCHAR(100) NOT NULL,
    elevasi_rata_rata_m NUMERIC(6,2),
    geom                GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST (geom);

-- ---------------------------------------------------------------------
-- Titik infrastruktur penting (sekolah, puskesmas, pelabuhan, permukiman)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS infrastructure (
    id              SERIAL PRIMARY KEY,
    nama            VARCHAR(150) NOT NULL,
    jenis           VARCHAR(50) NOT NULL, -- sekolah | puskesmas | pelabuhan | permukiman
    village_id      INTEGER REFERENCES villages(id),
    geom            GEOMETRY(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_infrastructure_geom ON infrastructure USING GIST (geom);

-- ---------------------------------------------------------------------
-- Hasil prediksi genangan (output Flood Simulation Engine)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flood_prediction (
    id                          BIGSERIAL PRIMARY KEY,
    village_id                  INTEGER NOT NULL REFERENCES villages(id),
    waktu_mulai                 TIMESTAMPTZ NOT NULL,
    waktu_puncak                TIMESTAMPTZ NOT NULL,
    durasi_jam                  NUMERIC(5,2),
    tinggi_genangan_min_cm      NUMERIC(6,2),
    tinggi_genangan_max_cm      NUMERIC(6,2),
    luas_genangan_ha            NUMERIC(10,2),
    volume_genangan_m3          NUMERIC(14,2),
    tingkat_risiko              VARCHAR(20) NOT NULL, -- aman | waspada | siaga | awas
    geom_genangan               GEOMETRY(MultiPolygon, 4326),
    model_version               VARCHAR(50) NOT NULL DEFAULT 'tahap1-rule-based',
    dibuat_pada                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_flood_prediction_waktu ON flood_prediction (waktu_mulai);
CREATE INDEX IF NOT EXISTS idx_flood_prediction_geom ON flood_prediction USING GIST (geom_genangan);

-- ---------------------------------------------------------------------
-- Basis data kejadian rob historis (untuk validasi & training ML)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historical_events (
    id                      SERIAL PRIMARY KEY,
    village_id              INTEGER REFERENCES villages(id),
    tanggal_kejadian        DATE NOT NULL,
    tinggi_genangan_cm      NUMERIC(6,2),
    durasi_jam              NUMERIC(5,2),
    sumber_laporan          VARCHAR(150), -- BPBD, warga, media, dll
    catatan                 TEXT,
    dibuat_pada             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Log pengiriman peringatan dini
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warning_logs (
    id                  BIGSERIAL PRIMARY KEY,
    village_id          INTEGER REFERENCES villages(id),
    tingkat_risiko      VARCHAR(20) NOT NULL,
    pesan               TEXT NOT NULL,
    kanal               VARCHAR(30) NOT NULL, -- whatsapp | telegram | email | webpush
    status_kirim        VARCHAR(20) NOT NULL DEFAULT 'terkirim', -- terkirim | gagal
    dikirim_pada        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_warning_logs_waktu ON warning_logs (dikirim_pada);
