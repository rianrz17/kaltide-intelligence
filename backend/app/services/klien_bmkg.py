"""
Klien BMKG
==========
Wrapper untuk mengambil data prakiraan cuaca (curah hujan, angin, dll) dari
API BMKG resmi: https://data.bmkg.go.id/prakiraan-cuaca

API ini GRATIS dan TERBUKA -- tidak perlu API key/registrasi. Batas akses:
60 permintaan per menit per alamat IP.

Dipakai parameter `adm3` (kode kecamatan), BUKAN `adm4` (kode desa/kelurahan)
-- satu request adm3 mengembalikan data untuk SEMUA desa/kelurahan di
kecamatan itu sekaligus (lebih hemat request dibanding adm4 yang per-desa).
Kita ambil entri pertama (`data[0]`) sebagai wakil kecamatan tersebut.

CATATAN PENTING soal data yang tersedia:
- Endpoint ini TIDAK menyediakan data tekanan udara. `tekanan_udara_hpa`
  akan selalu None -- ini bukan bug, memang tidak ada di sumbernya.
- Kecepatan angin (`ws`) dari BMKG dalam satuan KM/JAM, sudah dikonversi
  ke M/S di sini agar konsisten dengan skema DataCuaca kita.
- Response API untuk `adm3` berbentuk: {"data": [{"lokasi": {...},
  "cuaca": [[...hari1...], [...hari2...], [...hari3...]]}, ...satu per
  desa...]}. Kita ambil data[0] saja (desa pertama) sebagai representasi
  kecamatan.

Kode kecamatan (adm3) untuk 6 wilayah MVP KALTIDE, dikonfirmasi dari
kodewilayah.id (berdasarkan Kepmendagri terbaru) pada Juli 2026:
"""

from datetime import datetime

import httpx

from app.core.config import dapatkan_pengaturan
from app.models.skema import DataCuaca

pengaturan = dapatkan_pengaturan()

# Kode wilayah tingkat kecamatan (adm3), key harus SAMA dengan nama
# kecamatan di tabel `villages` (seed_mvp.sql & seed_ekspansi.sql).
PEMETAAN_KODE_WILAYAH: dict[str, str] = {
    "Anggana": "64.02.04",
    "Balikpapan Kota": "64.71.06",
    "Penajam": "64.09.01",
    "Samarinda Ilir": "64.72.04",
    "Bontang Utara": "64.74.01",
    "Tanjung Redeb": "64.03.05",
}


class KlienBMKG:
    """Klien HTTP untuk berkomunikasi dengan API BMKG (data.bmkg.go.id)."""

    BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

    def ambil_forecast_by_kode_kecamatan(self, kode_kecamatan: str) -> list[DataCuaca]:
        """
        Mengambil prakiraan cuaca 3 hari untuk satu kecamatan (adm3).
        Mengambil desa pertama dalam daftar sebagai representasi kecamatan.
        """
        with httpx.Client(timeout=15.0) as klien:
            respons = klien.get(self.BASE_URL, params={"adm3": kode_kecamatan})
            respons.raise_for_status()
            mentah = respons.json()

        daftar_data = mentah.get("data", [])
        if not daftar_data:
            return []

        # Ambil desa pertama sebagai representasi kecamatan
        return self._parse_response(kode_kecamatan, daftar_data[0])

    def ambil_forecast(self, stasiun_id: str, jumlah_hari: int = 3) -> list[DataCuaca]:
        """
        Kompatibilitas dengan ForecastEngine yang sudah ada: menerima
        `stasiun_id` (nama kecamatan) dan `jumlah_hari`, lalu mencari kode
        kecamatannya di PEMETAAN_KODE_WILAYAH.

        `jumlah_hari` tidak benar-benar membatasi API (BMKG selalu kirim 3
        hari x 8 data/hari = ~24 titik), hasil di sini dipotong sesuai
        jumlah_hari*8.
        """
        kode_kecamatan = PEMETAAN_KODE_WILAYAH.get(stasiun_id)
        if kode_kecamatan is None:
            raise ValueError(
                f"Kode kecamatan BMKG untuk '{stasiun_id}' belum ada di "
                "PEMETAAN_KODE_WILAYAH (backend/app/services/klien_bmkg.py)."
            )

        hasil = self.ambil_forecast_by_kode_kecamatan(kode_kecamatan)
        return hasil[: jumlah_hari * 8]

    @staticmethod
    def _parse_response(stasiun_id: str, data_satu_desa: dict) -> list[DataCuaca]:
        """
        Mengubah satu entri data desa (dari response adm3, nested per hari)
        menjadi list DataCuaca terstandardisasi.
        """
        hasil: list[DataCuaca] = []

        # Struktur: {"lokasi": {...}, "cuaca": [[entri, entri, ...], [...], [...]]}
        for hari in data_satu_desa.get("cuaca", []):
            for entri in hari:
                kecepatan_angin_kmh = entri.get("ws")
                kecepatan_angin_ms = (
                    round(kecepatan_angin_kmh / 3.6, 2) if kecepatan_angin_kmh is not None else None
                )

                hasil.append(
                    DataCuaca(
                        stasiun_id=stasiun_id,
                        waktu=datetime.fromisoformat(entri["local_datetime"]),
                        curah_hujan_mm=float(entri.get("tp", 0.0) or 0.0),
                        kecepatan_angin_ms=kecepatan_angin_ms,
                        arah_angin_derajat=entri.get("wd_deg"),
                        tekanan_udara_hpa=None,  # BMKG tidak menyediakan data ini di endpoint ini
                    )
                )

        return hasil
