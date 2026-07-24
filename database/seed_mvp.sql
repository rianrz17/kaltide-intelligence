-- =====================================================================
-- KALTIDE Intelligence - Seed Data Wilayah MVP
-- Balikpapan | Penajam Paser Utara (PPU) | Kutai Kartanegara (Muara Jawa-Anggana)
-- =====================================================================
--
-- PENTING - BACA DULU SEBELUM PAKAI:
-- Koordinat di file ini adalah REFERENSI AWAL (pusat kecamatan, pelabuhan,
-- kantor pemerintahan) yang dipakai supaya sistem bisa langsung diuji coba
-- end-to-end. INI BUKAN data stasiun resmi BMKG/PUSHIDROSAL.
--
-- SEBELUM VALIDASI LAPANGAN / PRODUKSI, tim WAJIB mengganti/melengkapi:
--   1. Koordinat & kode stasiun AWS/ARG      -> https://data.bmkg.go.id
--   2. Koordinat tide gauge resmi            -> PUSHIDROSAL / Dishidros TNI AL
--   3. elevasi_rata_rata_m per desa           -> ekstraksi raster DEMNAS
--                                                (lihat data/dem/ + dem_tiles)
--
-- Jalankan setelah schema.sql:
--   psql -h localhost -U kaltide -d kaltide -f database/seed_mvp.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. VILLAGES (level kecamatan untuk sementara, sambil menunggu data
--    batas desa/kelurahan resmi dari BIG/Kemendagri)
--    Catatan: geom di bawah adalah TITIK pusat kecamatan (Point) yang
--    dibungkus jadi polygon buffer kecil, HANYA untuk keperluan uji coba.
--    Ganti dengan polygon batas administrasi resmi saat tersedia.
-- ---------------------------------------------------------------------

-- Fungsi bantu: buat polygon buffer kecil (~2km) dari 1 titik pusat,
-- supaya kolom geom (MultiPolygon) di tabel villages terisi valid.
-- (Buffer dalam derajat, kasar, hanya untuk placeholder MVP.)

INSERT INTO villages (nama, kecamatan, kabupaten_kota, elevasi_rata_rata_m, geom)
VALUES
    -- === KOTA BALIKPAPAN ===
    ('Balikpapan Kota', 'Balikpapan Kota', 'Kota Balikpapan', 3.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.831, -1.267), 4326), 0.02))),
    ('Balikpapan Selatan', 'Balikpapan Selatan', 'Kota Balikpapan', 2.5,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.827, -1.283), 4326), 0.02))),
    ('Balikpapan Barat', 'Balikpapan Barat', 'Kota Balikpapan', 2.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.767, -1.183), 4326), 0.02))),

    -- === PENAJAM PASER UTARA (termasuk kawasan IKN) ===
    ('Penajam', 'Penajam', 'Penajam Paser Utara', 2.5,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.735, -1.302), 4326), 0.02))),
    ('Waru', 'Waru', 'Penajam Paser Utara', 3.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.699, -1.199), 4326), 0.02))),
    ('Sepaku', 'Sepaku', 'Penajam Paser Utara', 15.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(116.900, -0.950), 4326), 0.02))),

    -- === KUTAI KARTANEGARA (fokus pesisir: Muara Jawa - Anggana) ===
    ('Anggana', 'Anggana', 'Kutai Kartanegara', 1.5,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.240, -0.478), 4326), 0.02))),
    ('Muara Jawa', 'Muara Jawa', 'Kutai Kartanegara', 1.8,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.108, -0.663), 4326), 0.02))),
    ('Samboja', 'Samboja', 'Kutai Kartanegara', 4.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.020, -0.980), 4326), 0.02)))
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------
-- 2. STATIONS (stasiun observasi - PLACEHOLDER, ganti dengan data resmi)
-- ---------------------------------------------------------------------

INSERT INTO stations (id, nama, jenis, kecamatan, kabupaten_kota, geom, aktif)
VALUES
    ('balikpapan-pelabuhan', 'Referensi Pelabuhan Semayang Balikpapan (placeholder tide gauge)',
        'tide_gauge', 'Balikpapan Kota', 'Kota Balikpapan',
        ST_SetSRID(ST_MakePoint(116.831, -1.267), 4326), true),

    ('balikpapan-kariangau', 'Referensi Pelabuhan Kariangau (placeholder tide gauge)',
        'tide_gauge', 'Balikpapan Barat', 'Kota Balikpapan',
        ST_SetSRID(ST_MakePoint(116.767, -1.183), 4326), true),

    ('ppu-penajam', 'Referensi Pelabuhan Feri Penajam (placeholder tide gauge)',
        'tide_gauge', 'Penajam', 'Penajam Paser Utara',
        ST_SetSRID(ST_MakePoint(116.735, -1.302), 4326), true),

    ('ppu-aws-01', 'Referensi AWS Penajam (placeholder AWS)',
        'aws', 'Penajam', 'Penajam Paser Utara',
        ST_SetSRID(ST_MakePoint(116.744, -1.246), 4326), true),

    ('kukar-anggana-01', 'Referensi AWS Anggana (placeholder AWS)',
        'aws', 'Anggana', 'Kutai Kartanegara',
        ST_SetSRID(ST_MakePoint(117.240, -0.478), 4326), true),

    ('kukar-muarajawa-01', 'Referensi AWS Muara Jawa (placeholder AWS)',
        'aws', 'Muara Jawa', 'Kutai Kartanegara',
        ST_SetSRID(ST_MakePoint(117.108, -0.663), 4326), true)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------
-- Verifikasi cepat setelah seed dijalankan:
--   SELECT id, nama, jenis, kecamatan FROM stations;
--   SELECT nama, kecamatan, kabupaten_kota, elevasi_rata_rata_m FROM villages;
-- ---------------------------------------------------------------------
