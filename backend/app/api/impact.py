"""Endpoint terkait analisis dampak infrastruktur (impact analysis)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import dapatkan_db
from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.services.klien_bmkg import KlienBMKG
from app.engines.intelligence_engine import IntelligenceEngine
from app.models.skema import DampakInfrastruktur

router = APIRouter(prefix="/impact", tags=["Impact"])

forecast_engine = ForecastEngine(klien_bmkg=KlienBMKG())
flood_engine = FloodSimulationEngine()
intelligence_engine = IntelligenceEngine()


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

    hasil: list[DampakInfrastruktur] = []
    for genangan in daftar_genangan:
        data_dampak = intelligence_engine.hitung_dampak_spasial(
            db, genangan, village_id, radius_buffer_m=radius_m
        )
        hasil.append(intelligence_engine.analisis_dampak(genangan, data_dampak))

    return hasil
