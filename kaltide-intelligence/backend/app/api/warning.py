"""Endpoint terkait peringatan dini (early warning)."""

from datetime import timedelta

from fastapi import APIRouter, Query

from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.intelligence_engine import IntelligenceEngine
from app.models.skema import PeringatanDini, TingkatRisiko

router = APIRouter(prefix="/warning", tags=["Warning"])

forecast_engine = ForecastEngine()
flood_engine = FloodSimulationEngine()
intelligence_engine = IntelligenceEngine()


@router.get("/{stasiun_id}", response_model=list[PeringatanDini])
def daftar_peringatan(
    stasiun_id: str,
    kecamatan: str = Query(..., description="Nama kecamatan, contoh: Anggana"),
    jumlah_hari: int = 3,
) -> list[PeringatanDini]:
    """Menghasilkan daftar peringatan dini (WASPADA/SIAGA/AWAS) untuk suatu kecamatan."""
    data_pasang = forecast_engine.prakiraan_pasang(stasiun_id, jumlah_hari)
    data_cuaca = forecast_engine.prakiraan_cuaca(stasiun_id, jumlah_hari)

    daftar_genangan = flood_engine.simulasikan(
        wilayah=stasiun_id,
        kecamatan=kecamatan,
        data_pasang=data_pasang,
        data_cuaca=data_cuaca,
    )

    peringatan: list[PeringatanDini] = []
    for genangan in daftar_genangan:
        if genangan.tingkat_risiko == TingkatRisiko.AMAN:
            continue
        peringatan.append(
            PeringatanDini(
                wilayah=genangan.wilayah,
                tingkat_risiko=genangan.tingkat_risiko,
                pesan=intelligence_engine.buat_narasi(genangan),
                waktu_terbit=genangan.waktu_mulai - timedelta(hours=3),
                berlaku_hingga=genangan.waktu_puncak + timedelta(hours=genangan.durasi_jam),
            )
        )
    return peringatan
