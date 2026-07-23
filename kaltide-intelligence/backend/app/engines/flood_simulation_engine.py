"""
Flood Simulation Engine
=======================
Menghitung potensi area genangan berdasarkan kombinasi:
    - elevasi (DEM)
    - tinggi muka air laut (pasang)
    - curah hujan
    - kapasitas drainase (disederhanakan sebagai faktor koreksi)

Tahap 1 (Rule-Based + GIS): menggunakan indeks rob sederhana, BUKAN model
hidrodinamika penuh. Formula ini akan digantikan/diperkaya oleh model
hidrodinamika sederhana pada Tahap 2, dan dikoreksi oleh Machine Learning
pada Tahap 3 (lihat docs/ROADMAP.md).
"""

from datetime import datetime, timedelta

from app.models.skema import DataCuaca, DataPasang, GenanganWilayah, TingkatRisiko

# Ambang batas indeks rob -> tingkat risiko.
# Indeks dihitung dari kombinasi tinggi pasang, curah hujan, dan elevasi rata-rata wilayah.
AMBANG_RISIKO = {
    TingkatRisiko.AMAN: 0.0,
    TingkatRisiko.WASPADA: 0.3,
    TingkatRisiko.SIAGA: 0.6,
    TingkatRisiko.AWAS: 0.85,
}


class FloodSimulationEngine:
    """Menghitung indeks & estimasi genangan rob untuk suatu wilayah/kecamatan."""

    def __init__(self, elevasi_rata_rata_m: float = 1.2) -> None:
        # Elevasi rata-rata idealnya diambil dari raster DEMNAS per-wilayah,
        # nilai default di bawah hanya contoh untuk wilayah pesisir rendah.
        self.elevasi_rata_rata_m = elevasi_rata_rata_m

    def hitung_indeks_rob(self, tinggi_pasang_m: float, curah_hujan_mm: float) -> float:
        """
        Menghitung indeks rob (0.0 - 1.0+) berdasarkan selisih tinggi pasang
        terhadap elevasi wilayah, ditambah kontribusi curah hujan.

        Semakin tinggi pasang mendekati/melebihi elevasi daratan, dan semakin
        deras hujan, semakin tinggi indeksnya.
        """
        selisih_elevasi = tinggi_pasang_m - self.elevasi_rata_rata_m
        komponen_pasang = max(0.0, selisih_elevasi) / max(0.5, self.elevasi_rata_rata_m)
        komponen_hujan = min(curah_hujan_mm / 50.0, 1.0)  # dinormalisasi ke 0-1, 50mm dianggap ekstrem

        indeks = (0.7 * komponen_pasang) + (0.3 * komponen_hujan)
        return round(max(0.0, indeks), 3)

    def klasifikasi_risiko(self, indeks: float) -> TingkatRisiko:
        """Mengubah nilai indeks rob menjadi kategori tingkat risiko."""
        if indeks >= AMBANG_RISIKO[TingkatRisiko.AWAS]:
            return TingkatRisiko.AWAS
        if indeks >= AMBANG_RISIKO[TingkatRisiko.SIAGA]:
            return TingkatRisiko.SIAGA
        if indeks >= AMBANG_RISIKO[TingkatRisiko.WASPADA]:
            return TingkatRisiko.WASPADA
        return TingkatRisiko.AMAN

    def simulasikan(
        self,
        wilayah: str,
        kecamatan: str,
        data_pasang: list[DataPasang],
        data_cuaca: list[DataCuaca],
    ) -> list[GenanganWilayah]:
        """
        Menghasilkan daftar prediksi genangan per periode waktu, dengan
        mencocokkan data pasang & cuaca berdasarkan waktu yang sama.
        """
        hasil: list[GenanganWilayah] = []
        peta_cuaca = {c.waktu.replace(minute=0, second=0, microsecond=0): c for c in data_cuaca}

        for titik_pasang in data_pasang:
            waktu_jam = titik_pasang.waktu.replace(minute=0, second=0, microsecond=0)
            cuaca_terdekat = peta_cuaca.get(waktu_jam)
            curah_hujan = cuaca_terdekat.curah_hujan_mm if cuaca_terdekat else 0.0

            indeks = self.hitung_indeks_rob(titik_pasang.tinggi_muka_air_m, curah_hujan)
            risiko = self.klasifikasi_risiko(indeks)

            if risiko == TingkatRisiko.AMAN:
                continue  # tidak dianggap sebagai kejadian genangan

            tinggi_genangan_cm = max(0.0, (titik_pasang.tinggi_muka_air_m - self.elevasi_rata_rata_m) * 100)

            hasil.append(
                GenanganWilayah(
                    wilayah=wilayah,
                    kecamatan=kecamatan,
                    tinggi_genangan_min_cm=round(tinggi_genangan_cm * 0.7, 1),
                    tinggi_genangan_max_cm=round(tinggi_genangan_cm * 1.3, 1),
                    waktu_mulai=titik_pasang.waktu,
                    waktu_puncak=titik_pasang.waktu + timedelta(hours=1),
                    durasi_jam=3.0,
                    tingkat_risiko=risiko,
                )
            )

        return hasil
