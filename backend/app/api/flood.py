"""Endpoint terkait simulasi genangan (flood) rob."""

from fastapi import APIRouter, Query

from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.models.skema import GenanganWilayah

router = APIRouter(prefix="/flood", tags=["Flood"])

forecast_engine = ForecastEngine()
flood_engine = FloodSimulationEngine()


@router.get("/prediksi/{stasiun_id}", response_model=list[GenanganWilayah])
def prediksi_genangan(
    stasiun_id: str,
    kecamatan: str = Query(..., description="Nama kecamatan, contoh: Anggana"),
    jumlah_hari: int = 3,
) -> list[GenanganWilayah]:
    """
    Menghasilkan prediksi genangan rob untuk suatu kecamatan berdasarkan
    kombinasi prakiraan pasang surut & curah hujan.

    Tahap 1 menggunakan Rule-Based + GIS (lihat FloodSimulationEngine).
    """
    data_pasang = forecast_engine.prakiraan_pasang(stasiun_id, jumlah_hari)
    data_cuaca = forecast_engine.prakiraan_cuaca(stasiun_id, jumlah_hari)

    return flood_engine.simulasikan(
        wilayah=stasiun_id,
        kecamatan=kecamatan,
        data_pasang=data_pasang,
        data_cuaca=data_cuaca,
    )
