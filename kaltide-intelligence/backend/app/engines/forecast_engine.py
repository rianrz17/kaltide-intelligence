"""
Forecast Engine
===============
Bertanggung jawab menghasilkan prakiraan parameter meteorologi (hujan, angin,
tekanan udara) dan pasang surut untuk 1-7 hari ke depan.

Tahap 1 (saat ini): mengambil data mentah dari BMKG & sumber pasang surut,
lalu menstandardisasi formatnya. Belum ada koreksi model fisik/ML — itu
akan ditambahkan pada Tahap 2 & 3 sesuai roadmap.
"""

from datetime import datetime, timedelta

from app.models.skema import DataCuaca, DataPasang


class ForecastEngine:
    """Menghasilkan prakiraan cuaca dan pasang surut untuk suatu wilayah."""

    def __init__(self, klien_bmkg=None, klien_pasang=None) -> None:
        # Klien eksternal disuntikkan (dependency injection) agar mudah di-mock saat testing.
        self.klien_bmkg = klien_bmkg
        self.klien_pasang = klien_pasang

    def prakiraan_cuaca(self, stasiun_id: str, jumlah_hari: int = 3) -> list[DataCuaca]:
        """
        Mengambil prakiraan cuaca dari BMKG untuk `jumlah_hari` ke depan.

        Catatan: jika `klien_bmkg` belum dikonfigurasi, fungsi ini mengembalikan
        data contoh (dummy) agar endpoint tetap bisa diuji tanpa koneksi API nyata.
        """
        if self.klien_bmkg is not None:
            return self.klien_bmkg.ambil_forecast(stasiun_id, jumlah_hari)

        return self._data_cuaca_dummy(stasiun_id, jumlah_hari)

    def prakiraan_pasang(self, stasiun_id: str, jumlah_hari: int = 3) -> list[DataPasang]:
        """
        Mengambil prakiraan pasang surut untuk `jumlah_hari` ke depan.

        Catatan: jika `klien_pasang` belum dikonfigurasi, fungsi ini mengembalikan
        data contoh (dummy) berbentuk gelombang sinusoidal sederhana.
        """
        if self.klien_pasang is not None:
            return self.klien_pasang.ambil_prediksi(stasiun_id, jumlah_hari)

        return self._data_pasang_dummy(stasiun_id, jumlah_hari)

    @staticmethod
    def _data_cuaca_dummy(stasiun_id: str, jumlah_hari: int) -> list[DataCuaca]:
        sekarang = datetime.now()
        hasil: list[DataCuaca] = []
        for jam in range(0, jumlah_hari * 24, 3):
            hasil.append(
                DataCuaca(
                    stasiun_id=stasiun_id,
                    waktu=sekarang + timedelta(hours=jam),
                    curah_hujan_mm=0.0,
                    kecepatan_angin_ms=3.5,
                    arah_angin_derajat=180.0,
                    tekanan_udara_hpa=1010.0,
                )
            )
        return hasil

    @staticmethod
    def _data_pasang_dummy(stasiun_id: str, jumlah_hari: int) -> list[DataPasang]:
        import math

        sekarang = datetime.now()
        hasil: list[DataPasang] = []
        for jam in range(0, jumlah_hari * 24):
            # Simulasi pasang surut sederhana: gelombang sinus dengan periode ~12.4 jam
            tinggi = 1.5 + 0.8 * math.sin((2 * math.pi / 12.4) * jam)
            hasil.append(
                DataPasang(
                    stasiun_id=stasiun_id,
                    waktu=sekarang + timedelta(hours=jam),
                    tinggi_muka_air_m=round(tinggi, 2),
                    jenis="prediksi",
                )
            )
        return hasil
