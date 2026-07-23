"""Endpoint ringkasan analitik untuk dashboard (kartu ringkasan)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.engines.flood_simulation_engine import FloodSimulationEngine
from app.engines.forecast_engine import ForecastEngine
from app.models.skema import TingkatRisiko

router = APIRouter(prefix="/analytics", tags=["Analytics"])

forecast_engine = ForecastEngine()
flood_engine = FloodSimulationEngine()


class RingkasanStatus(BaseModel):
    """Ringkasan status rob untuk kartu dashboard 'Status Rob Hari Ini'."""

    total_wilayah_terpantau: int
    wilayah_status_awas: int
    wilayah_status_siaga: int
    wilayah_status_waspada: int
    wilayah_status_aman: int


@router.get("/ringkasan", response_model=RingkasanStatus)
def ringkasan_status() -> RingkasanStatus:
    """
    Menghasilkan ringkasan jumlah wilayah per status risiko untuk hari ini.

    Tahap 1: dihitung langsung dari FloodSimulationEngine memakai data
    dummy/stasiun contoh. Pada tahap berikutnya, ini akan membaca dari
    tabel `flood_prediction` yang sudah diperbarui secara berkala.
    """
    from app.api.stations import DAFTAR_STASIUN_CONTOH

    hitung = {risiko: 0 for risiko in TingkatRisiko}

    for stasiun in DAFTAR_STASIUN_CONTOH:
        data_pasang = forecast_engine.prakiraan_pasang(stasiun.id, jumlah_hari=1)
        data_cuaca = forecast_engine.prakiraan_cuaca(stasiun.id, jumlah_hari=1)
        daftar_genangan = flood_engine.simulasikan(
            wilayah=stasiun.id,
            kecamatan=stasiun.kecamatan,
            data_pasang=data_pasang,
            data_cuaca=data_cuaca,
        )

        status_tertinggi = TingkatRisiko.AMAN
        urutan = [TingkatRisiko.AMAN, TingkatRisiko.WASPADA, TingkatRisiko.SIAGA, TingkatRisiko.AWAS]
        for genangan in daftar_genangan:
            if urutan.index(genangan.tingkat_risiko) > urutan.index(status_tertinggi):
                status_tertinggi = genangan.tingkat_risiko

        hitung[status_tertinggi] += 1

    return RingkasanStatus(
        total_wilayah_terpantau=len(DAFTAR_STASIUN_CONTOH),
        wilayah_status_awas=hitung[TingkatRisiko.AWAS],
        wilayah_status_siaga=hitung[TingkatRisiko.SIAGA],
        wilayah_status_waspada=hitung[TingkatRisiko.WASPADA],
        wilayah_status_aman=hitung[TingkatRisiko.AMAN],
    )
