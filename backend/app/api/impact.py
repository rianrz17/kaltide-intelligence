"""Endpoint terkait analisis dampak infrastruktur (impact analysis)."""

from fastapi import APIRouter, Query

from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.intelligence_engine import IntelligenceEngine
from app.models.skema import DampakInfrastruktur

router = APIRouter(prefix="/impact", tags=["Impact"])

forecast_engine = ForecastEngine()
flood_engine = FloodSimulationEngine()
intelligence_engine = IntelligenceEngine()


@router.get("/{stasiun_id}", response_model=list[DampakInfrastruktur])
def analisis_dampak(
    stasiun_id: str,
    kecamatan: str = Query(..., description="Nama kecamatan, contoh: Anggana"),
    jumlah_hari: int = 3,
) -> list[DampakInfrastruktur]:
    """
    Menghasilkan ringkasan dampak genangan terhadap infrastruktur
    (jalan, sekolah, puskesmas, pelabuhan, permukiman).

    Catatan: query spasial nyata terhadap layer infrastruktur (PostGIS)
    belum diimplementasikan pada Tahap 1 — lihat TODO di IntelligenceEngine.
    """
    data_pasang = forecast_engine.prakiraan_pasang(stasiun_id, jumlah_hari)
    data_cuaca = forecast_engine.prakiraan_cuaca(stasiun_id, jumlah_hari)

    daftar_genangan = flood_engine.simulasikan(
        wilayah=stasiun_id,
        kecamatan=kecamatan,
        data_pasang=data_pasang,
        data_cuaca=data_cuaca,
    )

    return [intelligence_engine.analisis_dampak(genangan) for genangan in daftar_genangan]
