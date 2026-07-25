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
        radius_buffer_m: float = 5000.0,
        geom_genangan_wkt: str | None = None,
    ) -> dict:
        """
        Menghitung dampak nyata terhadap infrastruktur memakai query spasial
        PostGIS, dengan mengiriskan area terdampak terhadap tabel
        `infrastructure` dan `roads`.

        area_terdampak ditentukan dengan dua cara:
        - Kalau `geom_genangan_wkt` DIISI (hasil SpatialFloodEngine, Tahap 2):
          area_terdampak = polygon genangan asli dari flood-fill DEM.
        - Kalau `geom_genangan_wkt` KOSONG (None, default -- perilaku lama
          Tahap 1 tidak berubah): area_terdampak = buffer dari titik pusat
          village, radius `radius_buffer_m` meter. Pendekatan sederhana
          selama tile DEM untuk wilayah ini belum tersedia di `dem_tiles`.

          Default radius diperbesar jadi 5 km (dari awalnya 500 m) karena
          titik koordinat di `seed_mvp.sql` masih PLACEHOLDER (pusat kecamatan
          administratif, bukan titik genangan presisi) -- radius kecil sering
          menghasilkan 0 dampak walau infrastrukturnya sebenarnya dekat.

        Membutuhkan tabel `infrastructure` dan `roads` sudah terisi data
        nyata (lihat docs/SUMBER_DATA_INFRASTRUKTUR.md). Jika tabel kosong,
        hasilnya akan 0 untuk semua kategori -- itu tandanya data belum
        diisi, BUKAN berarti tidak ada dampak.
        """
        area_terdampak_sql = (
            "SELECT ST_GeomFromText(:geom_wkt, 4326) AS area"
            if geom_genangan_wkt
            else """
                SELECT ST_Buffer(
                    ST_Centroid(geom)::geography, :radius
                )::geometry AS area
                FROM villages
                WHERE id = :village_id
            """
        )
        hasil = db.execute(
            text(
                f"""
                WITH area_terdampak AS (
                    {area_terdampak_sql}
                ),
                jalan_dampak AS (
                    SELECT COALESCE(SUM(ST_Length(r.geom::geography)), 0) / 1000.0 AS jalan_terdampak_km
                    FROM roads r, area_terdampak a
                    WHERE ST_Intersects(r.geom, a.area)
                ),
                infra_dampak AS (
                    SELECT
                        COUNT(*) FILTER (WHERE i.jenis = 'sekolah') AS sekolah_terdampak,
                        COUNT(*) FILTER (WHERE i.jenis = 'puskesmas') AS puskesmas_terdampak,
                        COUNT(*) FILTER (WHERE i.jenis = 'pelabuhan') AS pelabuhan_terdampak
                    FROM infrastructure i, area_terdampak a
                    WHERE ST_Intersects(i.geom, a.area)
                )
                SELECT
                    jalan_dampak.jalan_terdampak_km,
                    infra_dampak.sekolah_terdampak,
                    infra_dampak.puskesmas_terdampak,
                    infra_dampak.pelabuhan_terdampak
                FROM jalan_dampak, infra_dampak
                """
            ),
            {"village_id": village_id, "radius": radius_buffer_m, "geom_wkt": geom_genangan_wkt},
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

