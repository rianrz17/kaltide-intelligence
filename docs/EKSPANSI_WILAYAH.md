# Ekspansi Wilayah: Samarinda, Bontang, Berau

## Catatan Penting

Wilayah ini **di luar scope MVP awal** (Balikpapan-PPU-Kukar) yang tertulis
di dokumen konsep KALTIDE. Ditambahkan atas permintaan tim untuk memperluas
cakupan lebih awal. Perhatikan:

- **Samarinda**: risiko utamanya lebih ke **banjir sungai Mahakam** (limpasan
  air sungai), meski pengaruh pasang laut tetap terasa cukup jauh ke hulu
  Mahakam (sungai ini dipengaruhi pasang surut / tidal river). Model rob
  murni (Flood Simulation Engine kita saat ini) mungkin kurang pas untuk
  Samarinda dibanding wilayah pesisir murni seperti Bontang/Anggana --
  perlu dipertimbangkan lagi apakah butuh engine terpisah untuk banjir sungai.
- **Bontang**: kota pesisir, cocok dengan model rob yang sudah ada.
- **Berau**: kabupaten sangat luas (termasuk Kepulauan Derawan). Query di
  bawah fokus ke area **Tanjung Redeb** (ibu kota kabupaten) dan pesisir
  terdekat -- BUKAN seluruh kabupaten Berau.

## Query Overpass Turbo (3 Query Terpisah)

Buka https://overpass-turbo.eu untuk masing-masing, jalankan satu-satu
(supaya file exportnya juga terpisah per wilayah).

### 1. Samarinda

```
[out:json][timeout:60];
(
  node["amenity"="school"](-0.65,117.05,-0.30,117.30);
  node["amenity"="hospital"](-0.65,117.05,-0.30,117.30);
  node["amenity"="clinic"](-0.65,117.05,-0.30,117.30);
  node["healthcare"="center"](-0.65,117.05,-0.30,117.30);
  node["amenity"="ferry_terminal"](-0.65,117.05,-0.30,117.30);
  node["harbour"="yes"](-0.65,117.05,-0.30,117.30);
);
out geom;
```
Export sebagai: `data/raw/infrastruktur_osm_samarinda.geojson`

### 2. Bontang

```
[out:json][timeout:60];
(
  node["amenity"="school"](0.05,117.40,0.20,117.60);
  node["amenity"="hospital"](0.05,117.40,0.20,117.60);
  node["amenity"="clinic"](0.05,117.40,0.20,117.60);
  node["healthcare"="center"](0.05,117.40,0.20,117.60);
  node["amenity"="ferry_terminal"](0.05,117.40,0.20,117.60);
  node["harbour"="yes"](0.05,117.40,0.20,117.60);
);
out geom;
```
Export sebagai: `data/raw/infrastruktur_osm_bontang.geojson`

### 3. Berau (Tanjung Redeb & pesisir terdekat)

```
[out:json][timeout:60];
(
  node["amenity"="school"](1.90,117.20,2.40,117.80);
  node["amenity"="hospital"](1.90,117.20,2.40,117.80);
  node["amenity"="clinic"](1.90,117.20,2.40,117.80);
  node["healthcare"="center"](1.90,117.20,2.40,117.80);
  node["amenity"="ferry_terminal"](1.90,117.20,2.40,117.80);
  node["harbour"="yes"](1.90,117.20,2.40,117.80);
);
out geom;
```
Export sebagai: `data/raw/infrastruktur_osm_berau.geojson`

> Tips: sebelum export, lihat dulu peta hasil query-nya -- kalau titik yang
> muncul kelihatan jauh di luar kota (misal masuk ke hutan/laut kosong),
> berarti bounding box perlu disesuaikan lagi. Bounding box di atas adalah
> perkiraan area kota inti, boleh diperbesar/diperkecil sesuai kebutuhan.

## Setelah Ketiga File Diexport

Jalankan seed data kecamatan dulu (lihat `database/seed_ekspansi.sql`),
baru import tiap file:

```bash
"/c/Program Files/PostgreSQL/18/bin/psql" -U postgres -d kaltide -f database/seed_ekspansi.sql

python scripts/muat_data_osm.py --infrastruktur data/raw/infrastruktur_osm_samarinda.geojson
python scripts/muat_data_osm.py --infrastruktur data/raw/infrastruktur_osm_bontang.geojson
python scripts/muat_data_osm.py --infrastruktur data/raw/infrastruktur_osm_berau.geojson
```
