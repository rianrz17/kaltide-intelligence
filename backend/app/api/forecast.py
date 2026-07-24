"""Endpoint terkait prakiraan cuaca & pasang surut."""

from fastapi import APIRouter

from app.engines.forecast_engine import ForecastEngine
from app.services.klien_bmkg import KlienBMKG
from app.models.skema import DataCuaca, DataPasang

router = APIRouter(prefix="/forecast", tags=["Forecast"])
engine = ForecastEngine(klien_bmkg=KlienBMKG())
@router.get("/cuaca/{stasiun_id}", response_model=list[DataCuaca])
def ambil_prakiraan_cuaca(stasiun_id: str, jumlah_hari: int = 3) -> list[DataCuaca]:
    """Mengambil prakiraan cuaca (curah hujan, angin, tekanan) untuk 1-7 hari ke depan."""
    return engine.prakiraan_cuaca(stasiun_id, jumlah_hari)


@router.get("/pasang/{stasiun_id}", response_model=list[DataPasang])
def ambil_prakiraan_pasang(stasiun_id: str, jumlah_hari: int = 3) -> list[DataPasang]:
    """Mengambil prakiraan pasang surut untuk 1-7 hari ke depan."""
    return engine.prakiraan_pasang(stasiun_id, jumlah_hari)
