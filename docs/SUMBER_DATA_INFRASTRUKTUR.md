# Sumber Data Infrastruktur (Sekolah, Puskesmas, Pelabuhan, Jalan)

## Kenapa Tidak Otomatis dari Sini?

Idealnya kode kita langsung "menyedot" data OpenStreetMap secara otomatis.
Tapi **Overpass API (server publik OSM) memblokir akses otomatis/bot**
(lihat `robots.txt` mereka) — jadi proses ini harus dilakukan manual satu
kali oleh tim lewat web browser, memakai **Overpass Turbo**. Prosesnya
tetap cepat (hitungan menit) dan hasilnya bisa diverifikasi visual di
peta sebelum diimpor.

## Langkah 1: Ambil Data via Overpass Turbo

1. Buka **https://overpass-turbo.eu**
2. Copy-paste query di bawah ini ke kotak query (ganti bounding box sesuai
   kebutuhan — nilai di bawah mencakup Balikpapan, PPU, dan Kukar pesisir):

```
[out:json][timeout:60];
(
  node["amenity"="school"](−1.35,116.6,−0.4,117.3);
  node["amenity"="hospital"](−1.35,116.6,−0.4,117.3);
  node["amenity"="clinic"](−1.35,116.6,−0.4,117.3);
  node["healthcare"="center"](−1.35,116.6,−0.4,117.3);
  node["amenity"="ferry_terminal"](−1.35,116.6,−0.4,117.3);
  node["harbour"="yes"](−1.35,116.6,−0.4,117.3);
  way["highway"~"^(trunk|primary|secondary)$"](−1.35,116.6,−0.4,117.3);
);
out geom;
```

   > Catatan: kalau ada karakter tanda minus yang aneh saat copy-paste
   > (`−` vs `-`), ganti manual jadi tanda minus biasa di keyboard.

3. Klik tombol **Run** (▶) di Overpass Turbo
4. Setelah hasil muncul di peta, klik **Export** → **GeoJSON** → download filenya
5. Simpan sebagai `data/raw/infrastruktur_osm.geojson` dan
   `data/raw/jalan_osm.geojson` (pisahkan node infrastruktur dari way jalan,
   atau ekspor terpisah dengan query yang di-split jadi 2)

## Langkah 2: Verifikasi Data (Penting!)

Data OpenStreetMap dikumpulkan sukarelawan — kualitasnya bervariasi per
wilayah. **Sebelum dipakai untuk keputusan operasional**, cek dulu:

- Apakah jumlah sekolah/puskesmas yang muncul masuk akal dibanding data
  resmi Kemendikbud (referensi.data.kemdikbud.go.id) atau Kemenkes
  (fasyankes.kemkes.go.id / sirs.kemkes.go.id)?
- Apakah lokasi titik-titiknya benar secara visual di peta (tidak
  melenceng jauh)?

Kalau data OSM di wilayah Anda ternyata jarang/kosong (umum terjadi di
daerah yang belum banyak dipetakan sukarelawan), lengkapi manual dari:

- **Data Pokok Pendidikan (Dapodik)**: https://dapo.kemdikbud.go.id
- **Fasyankes Kemenkes**: https://fasyankes.kemkes.go.id
- **Satu Peta / Ina-Geoportal (BIG)**: https://tanahair.indonesia.go.id
  — punya layer resmi jalan, batas administrasi, dan beberapa infrastruktur

## Langkah 3: Impor ke Database

Setelah file GeoJSON siap di `data/raw/`, jalankan:

```bash
python scripts/muat_data_osm.py \
    --infrastruktur data/raw/infrastruktur_osm.geojson \
    --jalan data/raw/jalan_osm.geojson
```

Script ini akan mengklasifikasikan tag OSM (`amenity=school` →
`jenis='sekolah'`, dst) dan mengisi tabel `infrastructure` & `roads` di
PostGIS.

## Setelah Data Terisi

Endpoint `GET /impact/{stasiun_id}` di backend akan otomatis memakai data
ini lewat query spasial PostGIS (`IntelligenceEngine.hitung_dampak_spasial`)
— tidak perlu ubah kode lagi, cukup pastikan data infrastrukturnya sudah
masuk ke tabel `villages`, `infrastructure`, dan `roads`.

## Catatan Teknis: Kenapa Pakai Buffer Sementara?

Sampai Flood Simulation Engine Tahap 2 (model hidrodinamika berbasis DEM)
selesai dan bisa menghasilkan **polygon genangan aktual**, query dampak
saat ini memakai pendekatan sederhana: buffer radius (default 500 meter)
dari titik pusat kecamatan yang berstatus WASPADA/SIAGA/AWAS. Ini
perkiraan kasar, bukan area genangan sebenarnya — akan digantikan begitu
`flood_prediction.geom_genangan` (lihat `database/schema.sql`) mulai terisi
hasil simulasi nyata.
