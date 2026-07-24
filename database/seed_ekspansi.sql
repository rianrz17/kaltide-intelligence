-- =====================================================================
-- KALTIDE Intelligence - Seed Data Wilayah Ekspansi
-- Samarinda | Bontang | Berau (Tanjung Redeb)
-- =====================================================================
-- PENTING: sama seperti seed_mvp.sql, koordinat di sini adalah REFERENSI
-- (pusat kecamatan), BUKAN data batas administrasi resmi. Wajib diverifikasi
-- sebelum dipakai operasional. Lihat docs/EKSPANSI_WILAYAH.md untuk catatan
-- soal karakteristik masing-masing wilayah (Samarinda lebih ke banjir
-- sungai, bukan murni rob laut).
--
-- Jalankan setelah schema.sql & seed_mvp.sql:
--   psql -h localhost -U kaltide -d kaltide -f database/seed_ekspansi.sql
-- =====================================================================

INSERT INTO villages (nama, kecamatan, kabupaten_kota, elevasi_rata_rata_m, geom)
VALUES
    -- === KOTA SAMARINDA (pesisir Sungai Mahakam, bukan pesisir laut langsung) ===
    ('Samarinda Ilir', 'Samarinda Ilir', 'Kota Samarinda', 6.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.162, -0.495), 4326), 0.02))),
    ('Palaran', 'Palaran', 'Kota Samarinda', 5.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.196, -0.616), 4326), 0.02))),
    ('Sungai Kunjang', 'Sungai Kunjang', 'Kota Samarinda', 7.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.100, -0.502), 4326), 0.02))),

    -- === KOTA BONTANG (pesisir laut langsung) ===
    ('Bontang Utara', 'Bontang Utara', 'Kota Bontang', 2.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.485, 0.152), 4326), 0.02))),
    ('Bontang Selatan', 'Bontang Selatan', 'Kota Bontang', 1.8,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.500, 0.100), 4326), 0.02))),

    -- === KABUPATEN BERAU (fokus Tanjung Redeb & pesisir terdekat) ===
    ('Tanjung Redeb', 'Tanjung Redeb', 'Kabupaten Berau', 3.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.502, 2.152), 4326), 0.02))),
    ('Gunung Tabur', 'Gunung Tabur', 'Kabupaten Berau', 4.0,
        ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(117.535, 2.170), 4326), 0.02)))
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------
-- Verifikasi cepat setelah seed dijalankan:
--   SELECT nama, kecamatan, kabupaten_kota FROM villages
--   WHERE kabupaten_kota IN ('Kota Samarinda', 'Kota Bontang', 'Kabupaten Berau');
-- ---------------------------------------------------------------------
