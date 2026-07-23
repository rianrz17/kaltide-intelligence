"""
Intelligence Engine
===================
Mengubah hasil mentah Flood Simulation Engine menjadi analisis dampak
yang mudah dipahami: dampak terhadap infrastruktur, serta narasi ringkas
yang bisa langsung dipakai untuk notifikasi/peringatan dini.

Analisis dampak memakai QUERY SPASIAL POSTGIS sungguhan (ST_Intersects /
ST_Length) terhadap tabel `infrastructure` dan `roads`, BUKAN data contoh.
Lihat `hitung_dampak_spasial()` di bawah. Data infrastruktur itu sendiri
perlu diisi tim lebih dulu -- lihat docs/SUMBER_DATA_INFRASTRUKTUR.md
untuk cara mengambil data OpenStreetMap resmi lewat Overpass Turbo.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

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

    def hitung_dampak_spasial(
        self,
        db: Session,
        genangan: GenanganWilayah,
        village_id: int,
        radius_buffer_m: float = 500.0,
    ) -> dict:
        """
        Menghitung dampak nyata terhadap infrastruktur memakai query spasial
        PostGIS, dengan mengiriskan area sekitar desa/kecamatan terdampak
        (buffer dari titik pusat village, radius `radius_buffer_m` meter --
        pendekatan sederhana selama polygon genangan aktual dari Flood
        Simulation Engine Tahap 2 belum tersedia) terhadap tabel
        `infrastructure` dan `roads`.

        Membutuhkan tabel `infrastructure` dan `roads` sudah terisi data
        nyata (lihat docs/SUMBER_DATA_INFRASTRUKTUR.md). Jika tabel kosong,
        hasilnya akan 0 untuk semua kategori -- itu tandanya data belum
        diisi, BUKAN berarti tidak ada dampak.
        """
        hasil = db.execute(
            text(
                """
                WITH area_terdampak AS (
                    SELECT ST_Buffer(
                        ST_Centroid(geom)::geography, :radius
                    )::geometry AS area
                    FROM villages
                    WHERE id = :village_id
                )
                SELECT
                    COALESCE(SUM(ST_Length(r.geom::geography)) FILTER (
                        WHERE ST_Intersects(r.geom, (SELECT area FROM area_terdampak))
                    ), 0) / 1000.0 AS jalan_terdampak_km,
                    COUNT(*) FILTER (
                        WHERE i.jenis = 'sekolah'
                        AND ST_Intersects(i.geom, (SELECT area FROM area_terdampak))
                    ) AS sekolah_terdampak,
                    COUNT(*) FILTER (
                        WHERE i.jenis = 'puskesmas'
                        AND ST_Intersects(i.geom, (SELECT area FROM area_terdampak))
                    ) AS puskesmas_terdampak,
                    COUNT(*) FILTER (
                        WHERE i.jenis = 'pelabuhan'
                        AND ST_Intersects(i.geom, (SELECT area FROM area_terdampak))
                    ) AS pelabuhan_terdampak
                FROM infrastructure i
                FULL OUTER JOIN roads r ON true
                """
            ),
            {"village_id": village_id, "radius": radius_buffer_m},
        ).fetchone()

        if hasil is None:
            return {
                "jalan_terdampak_km": 0.0,
                "sekolah_terdampak": 0,
                "puskesmas_terdampak": 0,
                "pelabuhan_terdampak": 0,
                "rumah_terdampak": 0,
            }

        return {
            "jalan_terdampak_km": round(float(hasil.jalan_terdampak_km or 0), 2),
            "sekolah_terdampak": int(hasil.sekolah_terdampak or 0),
            "puskesmas_terdampak": int(hasil.puskesmas_terdampak or 0),
            "pelabuhan_terdampak": int(hasil.pelabuhan_terdampak or 0),
            "rumah_terdampak": 0,  # TODO: hitung dari landuse permukiman x kepadatan, lihat docs
        }

    def analisis_dampak(
        self,
        genangan: GenanganWilayah,
        data_infrastruktur: dict | None = None,
    ) -> DampakInfrastruktur:
        """
        Membungkus hasil query spasial (atau dict manual untuk testing/tanpa-DB)
        menjadi objek DampakInfrastruktur + narasi siap pakai.

        - Kalau `data_infrastruktur` diisi (mis. hasil dari `hitung_dampak_spasial`),
          nilai itu yang dipakai.
        - Kalau tidak diisi (mis. belum ada koneksi DB), nilai default 0 dipakai
          supaya endpoint tetap tidak error -- TAPI ini bukan berarti "aman",
          cuma berarti data belum tersedia untuk dianalisis.
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

