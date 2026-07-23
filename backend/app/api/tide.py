"""Endpoint khusus data pasang surut observasi/prediksi mentah."""

from fastapi import APIRouter

from app.engines.forecast_engine import ForecastEngine
from app.models.skema import DataPasang

router = APIRouter(prefix="/tide", tags=["Tide"])
engine = ForecastEngine()


@router.get("/{stasiun_id}", response_model=list[DataPasang])
def ambil_data_pasang(stasiun_id: str, jumlah_hari: int = 3) -> list[DataPasang]:
    """Mengambil data pasang surut (prediksi) untuk sebuah stasiun."""
    return engine.prakiraan_pasang(stasiun_id, jumlah_hari)
