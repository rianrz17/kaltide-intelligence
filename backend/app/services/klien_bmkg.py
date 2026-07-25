"""
Klien BMKG - Prakiraan Cuaca Publik
=====================================

PENTING - Riwayat perubahan pendekatan:
-----------------------------------------
Versi sebelumnya (update7) memakai parameter `adm3` (kode kecamatan) dengan
asumsi 1 request bisa mengembalikan data untuk SEMUA desa dalam kecamatan
tersebut. Asumsi ini SALAH dan sudah dikonfirmasi lewat pengujian langsung
ke API resmi BMKG (Juli 2026):

    curl "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm3=64.02.04.1"
    -> HTTP 301, redirect ke halaman dokumentasi (endpoint tidak aktif)

    curl "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=64.72.04.1001"
    -> HTTP 200 OK, JSON valid

Endpoint resmi BMKG HANYA mendukung `adm4` (kode desa/kelurahan tingkat IV).
Dokumentasi resmi (https://data.bmkg.go.id/prakiraan-cuaca/) memang dari awal
hanya menyebutkan adm4, tidak pernah menyebutkan adm3 untuk endpoint ini.

Konsekuensi: setiap kecamatan MVP diwakili oleh SATU desa/kelurahan pesisir
(bukan seluruh kecamatan). Desa dipilih berdasarkan dua kriteria:
  1. Posisi geografis benar-benar di tepi laut/sungai besar
  2. Divalidasi silang dengan catatan berita banjir rob 5 tahun terakhir
     (lihat komentar di masing-masing entri LOKASI_MVP di bawah)

Endpoint tidak memerlukan API key. Batas akses resmi: 60 permintaan/menit/IP.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
TIMEOUT_DETIK = 10

# ---------------------------------------------------------------------------
# 6 lokasi MVP KALTIDE - kode adm4 (desa/kelurahan), bukan adm3 (kecamatan)
# ---------------------------------------------------------------------------
# Setiap entri divalidasi dari dua sisi:
#   (a) geografis - desa ini benar-benar berbatasan langsung dengan laut/
#       sungai besar yang dipengaruhi pasang surut
#   (b) historis - ada catatan berita banjir rob nyata di lokasi ini,
#       bukan cuma asumsi dari nama tempat
LOKASI_MVP: dict[str, dict[str, str]] = {
    "Anggana": {
        "kode_adm4": "64.02.04.2002",
        "desa": "Muara Pantuan",
        "kecamatan": "Anggana",
        "kabupaten": "Kutai Kartanegara",
        "catatan": (
            "Desa di muara Sungai Mahakam, mayoritas penduduk nelayan/"
            "petambak. Dikenal sebagai 'desa pesisir' di Delta Mahakam."
        ),
    },
    "Balikpapan Kota": {
        "kode_adm4": "64.71.06.1003",
        "desa": "Klandasan Ulu",
        "kecamatan": "Balikpapan Kota",
        "kabupaten": "Kota Balikpapan",
        "catatan": (
            "Lokasi Pantai Kemala & Pantai Melawai, berhadapan langsung "
            "dengan Selat Makassar. BMKG mengeluarkan peringatan rob "
            "berskala kota (bukan per-kelurahan) untuk kawasan Balikpapan "
            "beberapa kali per tahun (mis. pasang 2.9m, Jul 2025)."
        ),
    },
    "Penajam": {
        "kode_adm4": "64.09.01.1004",
        "desa": "Lawe-Lawe",
        "kecamatan": "Penajam",
        "kabupaten": "Penajam Paser Utara",
        "catatan": (
            "Di bibir Teluk Balikpapan, lokasi Terminal Crude Oil Pertamina. "
            "Termasuk salah satu dari 4 kawasan yang disebut BMKG "
            "terpengaruh langsung pasang surut di perairan Balikpapan."
        ),
    },
    "Samarinda Ilir": {
        "kode_adm4": "64.72.04.1001",
        "desa": "Selili",
        "kecamatan": "Samarinda Ilir",
        "kabupaten": "Kota Samarinda",
        "catatan": (
            "Tepi Sungai Mahakam. Kode ini sudah teruji langsung "
            "(HTTP 200, respons JSON valid) saat debugging Juli 2026."
        ),
    },
    "Bontang Utara": {
        "kode_adm4": "64.74.01.1001",
        "desa": "Bontang Kuala",
        "kecamatan": "Bontang Utara",
        "kabupaten": "Kota Bontang",
        "catatan": (
            "Luas wilayah laut lebih besar dari daratan, sebagian rumah "
            "panggung di atas laut. 'Langganan rob' - tercatat di berita "
            "berulang kali: Feb 2023, Nov 2025, Jan 2026, Jul 2026. "
            "Menggantikan Api-Api (kecamatan sama) yang lebih sering "
            "muncul untuk banjir hujan campuran, bukan rob murni."
        ),
    },
    "Tanjung Redeb": {
        "kode_adm4": "64.03.05.1005",
        "desa": "Bugis",
        "kecamatan": "Tanjung Redeb",
        "kabupaten": "Berau",
        "catatan": (
            "Permukiman di atas Sungai Segah/Kelay, dibangun turun-temurun "
            "oleh nelayan Bugis. Warga rutin diingatkan waspada aktivitas "
            "di tepi sungai saat kondisi pasang."
        ),
    },
}


@dataclass
class PrakiraanCuaca:
    """Satu titik data prakiraan cuaca (per 3 jam)."""

    datetime_utc: datetime
    datetime_lokal: datetime
    suhu_celsius: float
    kelembapan_persen: float
    tutupan_awan_persen: float
    curah_hujan_mm: float
    kecepatan_angin_kmh: float
    arah_angin: str
    cuaca_deskripsi: str
    cuaca_deskripsi_en: str
    jarak_pandang_m: float


@dataclass
class HasilPrakiraan:
    """Hasil lengkap prakiraan cuaca untuk satu lokasi (adm4)."""

    nama_kecamatan_mvp: str  # key di LOKASI_MVP, mis. "Anggana"
    kode_adm4: str
    desa: str
    kecamatan_bmkg: str  # nama kecamatan menurut response BMKG
    kabupaten_kota: str
    provinsi: str
    lat: float
    lon: float
    prakiraan: list[PrakiraanCuaca]
    diambil_pada: datetime


class KesalahanKlienBMKG(Exception):
    """Dilempar jika request ke BMKG gagal atau responsnya tidak valid."""


class KlienBMKG:
    """Klien untuk mengambil prakiraan cuaca dari API publik BMKG.

    PENTING: pakai kode adm4 (desa), bukan adm3 (kecamatan). Lihat
    docstring modul ini untuk alasannya.
    """

    def __init__(self, timeout_detik: int = TIMEOUT_DETIK) -> None:
        self.timeout_detik = timeout_detik
        self._session = requests.Session()

    def ambil_prakiraan(self, kode_adm4: str) -> HasilPrakiraan:
        """Ambil prakiraan cuaca 3 hari untuk satu desa (adm4).

        Args:
            kode_adm4: kode wilayah tingkat IV, format "XX.XX.XX.XXXX"
                       (mis. "64.02.04.2002")

        Raises:
            KesalahanKlienBMKG: jika request gagal, timeout, atau response
                                  tidak sesuai format yang diharapkan.
        """
        try:
            respons = self._session.get(
                BASE_URL,
                params={"adm4": kode_adm4},
                timeout=self.timeout_detik,
            )
            respons.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise KesalahanKlienBMKG(
                f"Timeout mengambil data untuk adm4={kode_adm4} "
                f"setelah {self.timeout_detik} detik"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise KesalahanKlienBMKG(
                f"BMKG mengembalikan status error untuk adm4={kode_adm4}: "
                f"{exc.response.status_code}. Kemungkinan kode wilayah "
                f"salah/tidak terdaftar, atau endpoint sedang bermasalah."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise KesalahanKlienBMKG(
                f"Gagal terhubung ke BMKG untuk adm4={kode_adm4}: {exc}"
            ) from exc

        try:
            data = respons.json()
        except ValueError as exc:
            raise KesalahanKlienBMKG(
                f"Respons BMKG untuk adm4={kode_adm4} bukan JSON valid. "
                f"Endpoint mungkin sedang redirect ke halaman dokumentasi "
                f"(cek apakah ada perubahan pada BMKG)."
            ) from exc

        return self._urai_respons(kode_adm4, data)

    def ambil_semua_lokasi_mvp(self) -> dict[str, HasilPrakiraan]:
        """Ambil prakiraan untuk seluruh 6 lokasi MVP KALTIDE sekaligus.

        Mengembalikan dict {nama_kecamatan_mvp: HasilPrakiraan}.
        Kalau satu lokasi gagal, error dicatat di log tapi lokasi lain
        tetap diproses (tidak menghentikan seluruh batch).
        """
        hasil: dict[str, HasilPrakiraan] = {}
        for nama_mvp, info in LOKASI_MVP.items():
            kode = info["kode_adm4"]
            try:
                prakiraan = self.ambil_prakiraan(kode)
                prakiraan.nama_kecamatan_mvp = nama_mvp
                hasil[nama_mvp] = prakiraan
                logger.info(
                    "Berhasil ambil prakiraan %s (%s, adm4=%s)",
                    nama_mvp, info["desa"], kode,
                )
            except KesalahanKlienBMKG as exc:
                logger.error(
                    "Gagal ambil prakiraan %s (%s, adm4=%s): %s",
                    nama_mvp, info["desa"], kode, exc,
                )
        return hasil

    @staticmethod
    def _urai_respons(kode_adm4: str, data: dict[str, Any]) -> HasilPrakiraan:
        """Parsing respons adm4: SATU objek lokasi, bukan array per desa.

        Struktur respons adm4 (beda dari asumsi adm3 di update7):
            {
              "lokasi": {...},
              "data": [
                {
                  "lokasi": {...},
                  "cuaca": [[...], [...], [...]]   # 3 array (3 hari),
                                                     # tiap array isi ~8
                                                     # titik data (per 3 jam)
                }
              ]
            }
        """
        try:
            lokasi = data["lokasi"]
            blok_data = data["data"][0]
            hari_hari = blok_data["cuaca"]
        except (KeyError, IndexError, TypeError) as exc:
            raise KesalahanKlienBMKG(
                f"Struktur respons BMKG untuk adm4={kode_adm4} tidak "
                f"sesuai yang diharapkan: {exc}. Field yang ada: "
                f"{list(data.keys())}"
            ) from exc

        titik_data: list[PrakiraanCuaca] = []
        for hari in hari_hari:
            for titik in hari:
                titik_data.append(
                    PrakiraanCuaca(
                        datetime_utc=datetime.fromisoformat(titik["datetime"]),
                        datetime_lokal=datetime.fromisoformat(
                            titik["local_datetime"]
                        ),
                        suhu_celsius=titik["t"],
                        kelembapan_persen=titik["hu"],
                        tutupan_awan_persen=titik["tcc"],
                        curah_hujan_mm=titik["tp"],
                        kecepatan_angin_kmh=titik["ws"],
                        arah_angin=titik["wd"],
                        cuaca_deskripsi=titik["weather_desc"],
                        cuaca_deskripsi_en=titik["weather_desc_en"],
                        jarak_pandang_m=titik["vs"],
                    )
                )

        return HasilPrakiraan(
            nama_kecamatan_mvp="",  # diisi oleh pemanggil kalau perlu
            kode_adm4=kode_adm4,
            desa=lokasi.get("desa", ""),
            kecamatan_bmkg=lokasi.get("kecamatan", ""),
            kabupaten_kota=lokasi.get("kotkab", ""),
            provinsi=lokasi.get("provinsi", ""),
            lat=lokasi.get("lat", 0.0),
            lon=lokasi.get("lon", 0.0),
            prakiraan=titik_data,
            diambil_pada=datetime.now(),
        )


if __name__ == "__main__":
    # Contoh pakai + verifikasi manual cepat untuk semua 6 lokasi MVP.
    # Jalankan: python klien_bmkg.py
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    klien = KlienBMKG()
    semua_hasil = klien.ambil_semua_lokasi_mvp()

    print(f"\n{'=' * 60}")
    print(f"Berhasil ambil {len(semua_hasil)}/{len(LOKASI_MVP)} lokasi MVP")
    print(f"{'=' * 60}\n")

    for nama_mvp, hasil in semua_hasil.items():
        titik_terbaru = hasil.prakiraan[0] if hasil.prakiraan else None
        print(f"[{nama_mvp}] {hasil.desa}, {hasil.kecamatan_bmkg}")
        print(f"  Kode adm4  : {hasil.kode_adm4}")
        print(f"  Koordinat  : {hasil.lat}, {hasil.lon}")
        if titik_terbaru:
            print(
                f"  Cuaca kini : {titik_terbaru.cuaca_deskripsi} "
                f"({titik_terbaru.suhu_celsius}°C, "
                f"kelembapan {titik_terbaru.kelembapan_persen}%)"
            )
        print(f"  Total titik data: {len(hasil.prakiraan)}")
        print()
