# Kode Wilayah BMKG (adm3) untuk 6 Kecamatan MVP

## Status: SUDAH TERISI ✅

Kode kecamatan (adm3) untuk BMKG API sudah ditemukan dan diisi di
`backend/app/services/klien_bmkg.py`, dikonfirmasi dari beberapa sumber
independen (kodewilayah.id, situs kode pos resmi) pada Juli 2026:

| Kecamatan | Kode adm3 |
|-----------|-----------|
| Anggana | `64.02.04` |
| Balikpapan Kota | `64.71.06` |
| Penajam | `64.09.01` |
| Samarinda Ilir | `64.72.04` |
| Bontang Utara | `64.74.01` |
| Tanjung Redeb | `64.03.05` |

## Kenapa Pakai `adm3`, Bukan `adm4`?

BMKG punya 4 level kode wilayah:
- `adm1` = provinsi
- `adm2` = kabupaten/kota
- `adm3` = **kecamatan** ← yang kita pakai
- `adm4` = desa/kelurahan (paling detail, tapi 1 request cuma 1 desa)

Pakai `adm3` lebih hemat: satu request mengembalikan data untuk **semua**
desa/kelurahan dalam kecamatan itu sekaligus. Kode kita ambil desa
pertama dalam daftar sebagai wakil kecamatan.

## Verifikasi Sebelum Dipakai Operasional

Kode-kode di atas didapat dari situs pihak ketiga (bukan API resmi
Kemendagri langsung, karena situs pencarian resminya memblokir akses
otomatis). **Sebelum dipakai untuk keputusan operasional**, sebaiknya tim
verifikasi ulang salah satu cara:

```bash
curl "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm3=64.02.04"
```

Cek bagian `lokasi.kecamatan` di response -- harus bertuliskan "Anggana".
Kalau cocok, kodenya benar. Ulangi untuk 5 kode lainnya.

## Cara Pakai di Kode

```python
from app.engines.forecast_engine import ForecastEngine
from app.services.klien_bmkg import KlienBMKG

forecast_engine = ForecastEngine(klien_bmkg=KlienBMKG())
```

Ganti `ForecastEngine()` polos dengan itu di file-file endpoint
(`backend/app/api/forecast.py`, `flood.py`, `warning.py`, `impact.py`,
`analytics.py`) untuk mulai pakai data BMKG asli, bukan lagi dummy.

## Batasan yang Perlu Diingat

- Batas akses BMKG: 60 permintaan/menit per IP.
- BMKG **tidak menyediakan data tekanan udara** lewat endpoint ini --
  `tekanan_udara_hpa` akan selalu `None`.
- Response selalu 3 hari ke depan (tidak bisa diminta 1 atau 7 hari
  langsung dari BMKG) -- kode kita memotong hasil sesuai `jumlah_hari`.
- Kalau nanti tambah wilayah baru, cari kode adm3-nya dengan cara yang
  sama (cari "kodewilayah.id kecamatan <nama>" atau verifikasi via curl
  di atas), lalu tambahkan ke `PEMETAAN_KODE_WILAYAH`.
