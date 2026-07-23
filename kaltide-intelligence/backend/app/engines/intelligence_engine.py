"""
Intelligence Engine
===================
Mengubah hasil mentah Flood Simulation Engine menjadi analisis dampak
yang mudah dipahami: dampak terhadap infrastruktur, serta narasi ringkas
yang bisa langsung dipakai untuk notifikasi/peringatan dini.
"""

from app.models.skema import DampakInfrastruktur, GenanganWilayah, TingkatRisiko

NARASI_RISIKO = {
    TingkatRisiko.WASPADA: "berpotensi mengalami genangan ringan",
    TingkatRisiko.SIAGA: "berpotensi mengalami genangan yang cukup signifikan",
    TingkatRisiko.AWAS: "berpotensi mengalami genangan tinggi yang membahayakan",
}


class IntelligenceEngine:
    """Menghasilkan analisis dampak & narasi dari data genangan."""

    def buat_narasi(self, genangan: GenanganWilayah) -> str:
        """
        Menghasilkan narasi ringkas ala buletin BMKG, contoh:
        "Kecamatan Anggana berpotensi mengalami genangan 35-60 cm pada
        pukul 03.00-07.00 WITA."
        """
        jam_mulai = genangan.waktu_mulai.strftime("%H.%M")
        jam_selesai = genangan.waktu_puncak.strftime("%H.%M")
        deskripsi_risiko = NARASI_RISIKO.get(genangan.tingkat_risiko, "berpotensi mengalami genangan")

        return (
            f"Kecamatan {genangan.kecamatan} {deskripsi_risiko} "
            f"{genangan.tinggi_genangan_min_cm:.0f}-{genangan.tinggi_genangan_max_cm:.0f} cm "
            f"pada pukul {jam_mulai}-{jam_selesai} WITA."
        )

    def analisis_dampak(
        self,
        genangan: GenanganWilayah,
        data_infrastruktur: dict | None = None,
    ) -> DampakInfrastruktur:
        """
        Menghitung estimasi dampak terhadap infrastruktur.

        `data_infrastruktur` idealnya berasal dari query spasial (PostGIS)
        yang mengiriskan polygon genangan dengan layer jalan/sekolah/
        puskesmas/pelabuhan/permukiman. Untuk Tahap 1, nilai default 0
        dipakai jika data belum tersedia, sehingga endpoint tetap berjalan.
        """
        data_infrastruktur = data_infrastruktur or {}

        dampak = DampakInfrastruktur(
            wilayah=genangan.wilayah,
            jalan_terdampak_km=data_infrastruktur.get("jalan_terdampak_km", 0.0),
            sekolah_terdampak=data_infrastruktur.get("sekolah_terdampak", 0),
            puskesmas_terdampak=data_infrastruktur.get("puskesmas_terdampak", 0),
            pelabuhan_terdampak=data_infrastruktur.get("pelabuhan_terdampak", 0),
            rumah_terdampak=data_infrastruktur.get("rumah_terdampak", 0),
        )
        dampak.narasi = self.buat_narasi(genangan)
        return dampak
