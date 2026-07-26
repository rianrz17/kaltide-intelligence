"""Endpoint terkait analisis dampak infrastruktur (impact analysis)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import dapatkan_db
from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.services.klien_bmkg import KlienBMKG
from app.engines.intelligence_engine import IntelligenceEngine
from app.engines.spatial_flood_engine import SpatialFloodEngine
from app.models.skema import DampakInfrastruktur

router = APIRouter(prefix="/impact", tags=["Impact"])

forecast_engine = ForecastEngine(klien_bmkg=KlienBMKG())
flood_engine = FloodSimulationEngine()
intelligence_engine = IntelligenceEngine()
spatial_flood_engine = SpatialFloodEngine()


@router.get("/{stasiun_id}", response_model=list[DampakInfrastruktur])
def analisis_dampak(
    stasiun_id: str,
    kecamatan: str = Query(..., description="Nama kecamatan, contoh: Anggana"),
    jumlah_hari: int = 3,
    radius_m: float = Query(
        5000.0,
        description=(
            "Radius buffer (meter) dari titik pusat kecamatan untuk mencari "
            "infrastruktur terdampak. Default 5000m karena koordinat kecamatan "
            "di seed_mvp.sql masih placeholder. Perkecil (mis. 500-1000) "
            "setelah data koordinat & polygon genangan lebih presisi."
        ),
    ),
    db: Session = Depends(dapatkan_db),
) -> list[DampakInfrastruktur]:
    """
    Menghasilkan ringkasan dampak genangan terhadap infrastruktur
    (jalan, sekolah, puskesmas, pelabuhan) memakai QUERY SPASIAL POSTGIS
    sungguhan terhadap tabel `infrastructure` dan `roads`.

    Catatan: hasil akan menunjukkan 0 untuk semua kategori jika tabel
    `infrastructure`/`roads` belum diisi data nyata untuk kecamatan ini,
    ATAU jika `radius_m` terlalu kecil untuk menjangkau infrastruktur
    terdekat. Lihat docs/SUMBER_DATA_INFRASTRUKTUR.md untuk cara mengisi
    data tersebut.
    """
    data_pasang = forecast_engine.prakiraan_pasang(stasiun_id, jumlah_hari)
    data_cuaca = forecast_engine.prakiraan_cuaca(stasiun_id, jumlah_hari)

    daftar_genangan = flood_engine.simulasikan(
        wilayah=stasiun_id,
        kecamatan=kecamatan,
        data_pasang=data_pasang,
        data_cuaca=data_cuaca,
    )

    baris_village = db.execute(
        text("SELECT id FROM villages WHERE kecamatan = :kecamatan LIMIT 1"),
        {"kecamatan": kecamatan},
    ).fetchone()

    if baris_village is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Kecamatan '{kecamatan}' belum ada di tabel villages. "
                "Jalankan database/seed_mvp.sql dulu, atau tambahkan datanya."
            ),
        )

    village_id = baris_village.id

    # Cari tile DEM untuk wilayah ini SEKALI di luar loop (tidak berubah per titik waktu).
    # None kalau dem_tiles masih kosong (DEMNAS belum diunggah) -- itu tanda "belum siap",
    # BUKAN error, endpoint tetap jalan dengan fallback buffer seperti Tahap 1.
    dem_path = spatial_flood_engine.cari_tile_dem(db, village_id)

    # Muat raster DEM ke memori SEKALI (bukan di dalam loop) -- optimasi performa.
    # File DEM bisa ~90MB (tile gabungan), dan sebelumnya dibuka ulang dari disk
    # untuk SETIAP titik waktu genangan (bisa 6-30x per request). dem_terload
    # menyimpan array elevasi + seed_mask yang sudah dihitung, dipakai ulang untuk
    # tiap water_level_m berbeda tanpa baca disk lagi.
    dem_terload = None
    if dem_path:
        try:
            dem_terload = spatial_flood_engine.muat_dem(dem_path)
        except Exception:
            # File rusak/tidak terbaca -- fallback ke buffer, jangan bikin seluruh
            # endpoint error. TODO: logging, bukan silent.
            dem_terload = None

    # PENTING: tile DEM sering mencakup beberapa kecamatan sekaligus (mosaic gabungan
    # beberapa tile grid). Terbukti empiris polygon flood-fill bisa 13-16x lebih luas
    # dari kecamatan itu sendiri kalau tidak dibatasi -- area dataran rendah/delta
    # membuat genangan terhubung menyebar jauh ke kecamatan tetangga. Ambil buffer
    # WKT di sekitar village SEKALI di luar loop, pakai radius yang sama dengan
    # fallback buffer (radius_m), supaya semantik "area terdampak" konsisten antara
    # mode fallback dan mode DEM asli.
    clip_geom_wkt: str | None = None
    if dem_terload is not None:
        baris_clip = db.execute(
            text(
                "SELECT ST_AsText(ST_Buffer(geom::geography, :radius)::geometry) AS wkt "
                "FROM villages WHERE id = :village_id"
            ),
            {"village_id": village_id, "radius": radius_m},
        ).fetchone()
        clip_geom_wkt = baris_clip.wkt if baris_clip else None

    hasil: list[DampakInfrastruktur] = []
    for genangan in daftar_genangan:
        geom_genangan_wkt: str | None = None

        if dem_terload is not None and genangan.tinggi_pasang_m is not None:
            try:
                water_level = spatial_flood_engine.hitung_water_level(
                    tinggi_pasang_m=genangan.tinggi_pasang_m,
                    curah_hujan_mm=0.0,  # TODO: sambungkan curah hujan per titik waktu, lihat catatan
                )
                hasil_spasial = spatial_flood_engine.buat_polygon_genangan(
                    dem_terload, water_level["tinggi_muka_air_m"], clip_geom_wkt=clip_geom_wkt
                )
                geom_genangan_wkt = hasil_spasial.geom_wkt
            except Exception:
                # Flood-fill gagal (mis. geometry tidak valid) -- fallback ke
                # buffer, JANGAN sampai satu titik waktu bermasalah bikin seluruh
                # endpoint /impact error. Idealnya di-log, bukan silent -- lihat TODO logging.
                geom_genangan_wkt = None

        data_dampak = intelligence_engine.hitung_dampak_spasial(
            db, genangan, village_id, radius_buffer_m=radius_m, geom_genangan_wkt=geom_genangan_wkt
        )
        hasil.append(intelligence_engine.analisis_dampak(genangan, data_dampak))

    return hasil
