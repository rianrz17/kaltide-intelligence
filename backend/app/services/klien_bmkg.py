"""
Klien BMKG
==========
Wrapper sederhana untuk mengambil data prakiraan cuaca (NDF - Numerical
Data Forecast) dari API BMKG.

CATATAN: endpoint & format response di bawah ini bersifat contoh/placeholder.
Sesuaikan `base_url`, path endpoint, dan parsing response dengan dokumentasi
resmi API BMKG yang digunakan tim (mis. https://data.bmkg.go.id).
"""

from datetime import datetime

import httpx

from app.core.config import dapatkan_pengaturan
from app.models.skema import DataCuaca

pengaturan = dapatkan_pengaturan()


class KlienBMKG:
    """Klien HTTP untuk berkomunikasi dengan API BMKG."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or pengaturan.bmkg_api_base_url
        self.api_key = api_key or pengaturan.bmkg_api_key

    def ambil_forecast(self, stasiun_id: str, jumlah_hari: int = 3) -> list[DataCuaca]:
        """
        Mengambil prakiraan cuaca untuk sebuah stasiun/wilayah.

        TODO: ganti path & parsing sesuai skema resmi API BMKG yang dipakai.
        """
        parameter = {"adm4": stasiun_id}
        header = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        with httpx.Client(timeout=10.0) as klien:
            respons = klien.get(f"{self.base_url}/publik/prakiraan-cuaca", params=parameter, headers=header)
            respons.raise_for_status()
            mentah = respons.json()

        return self._parse_response(stasiun_id, mentah)

    @staticmethod
    def _parse_response(stasiun_id: str, mentah: dict) -> list[DataCuaca]:
        """Mengubah response JSON mentah BMKG menjadi list DataCuaca terstandardisasi."""
        hasil: list[DataCuaca] = []
        for entri in mentah.get("data", []):
            hasil.append(
                DataCuaca(
                    stasiun_id=stasiun_id,
                    waktu=datetime.fromisoformat(entri["local_datetime"]),
                    curah_hujan_mm=float(entri.get("tp", 0.0)),
                    kecepatan_angin_ms=entri.get("ws"),
                    arah_angin_derajat=entri.get("wd_deg"),
                    tekanan_udara_hpa=entri.get("pressure"),
                )
            )
        return hasil
