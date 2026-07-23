"""
Klien Data Pasang Surut
========================
Wrapper untuk mengambil data prediksi/observasi pasang surut, baik dari
API PUSHIDROSAL maupun dari tide gauge lokal.

CATATAN: seperti klien_bmkg.py, endpoint di bawah ini adalah placeholder.
Sesuaikan dengan sumber data pasang surut resmi yang tersedia untuk tim.
"""

from datetime import datetime

import httpx

from app.core.config import dapatkan_pengaturan
from app.models.skema import DataPasang

pengaturan = dapatkan_pengaturan()


class KlienPasang:
    """Klien HTTP untuk mengambil data pasang surut."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or pengaturan.tide_api_base_url
        self.api_key = api_key or pengaturan.tide_api_key

    def ambil_prediksi(self, stasiun_id: str, jumlah_hari: int = 3) -> list[DataPasang]:
        """
        Mengambil prediksi pasang surut untuk sebuah stasiun tide gauge.

        TODO: sesuaikan path & parsing dengan API PUSHIDROSAL/tide gauge
        yang sebenarnya digunakan.
        """
        if not self.base_url:
            raise RuntimeError(
                "TIDE_API_BASE_URL belum dikonfigurasi. "
                "Set nilainya di .env atau gunakan data dummy dari ForecastEngine."
            )

        parameter = {"station": stasiun_id, "days": jumlah_hari}
        header = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        with httpx.Client(timeout=10.0) as klien:
            respons = klien.get(f"{self.base_url}/tide/prediction", params=parameter, headers=header)
            respons.raise_for_status()
            mentah = respons.json()

        return self._parse_response(stasiun_id, mentah)

    @staticmethod
    def _parse_response(stasiun_id: str, mentah: dict) -> list[DataPasang]:
        hasil: list[DataPasang] = []
        for entri in mentah.get("predictions", []):
            hasil.append(
                DataPasang(
                    stasiun_id=stasiun_id,
                    waktu=datetime.fromisoformat(entri["t"]),
                    tinggi_muka_air_m=float(entri["v"]),
                    jenis="prediksi",
                )
            )
        return hasil
