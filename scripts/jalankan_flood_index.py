"""
Script CLI: Jalankan Flood Index Engine
=========================================
Berguna untuk menguji cepat Flood Simulation Engine tanpa perlu
menjalankan seluruh backend/API. Menggunakan data dummy dari ForecastEngine
jika API BMKG/pasang belum dikonfigurasi.

Contoh pemakaian:
    python scripts/jalankan_flood_index.py --stasiun anggana-01 --kecamatan Anggana
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.engines.flood_simulation_engine import FloodSimulationEngine  # noqa: E402
from app.engines.forecast_engine import ForecastEngine  # noqa: E402
from app.engines.intelligence_engine import IntelligenceEngine  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Jalankan simulasi indeks rob (Tahap 1).")
    parser.add_argument("--stasiun", required=True, help="ID stasiun, contoh: anggana-01")
    parser.add_argument("--kecamatan", required=True, help="Nama kecamatan, contoh: Anggana")
    parser.add_argument("--hari", type=int, default=3, help="Jumlah hari prakiraan (1-7)")
    argumen = parser.parse_args()

    forecast_engine = ForecastEngine()
    flood_engine = FloodSimulationEngine()
    intelligence_engine = IntelligenceEngine()

    data_pasang = forecast_engine.prakiraan_pasang(argumen.stasiun, argumen.hari)
    data_cuaca = forecast_engine.prakiraan_cuaca(argumen.stasiun, argumen.hari)

    daftar_genangan = flood_engine.simulasikan(
        wilayah=argumen.stasiun,
        kecamatan=argumen.kecamatan,
        data_pasang=data_pasang,
        data_cuaca=data_cuaca,
    )

    if not daftar_genangan:
        print(f"Tidak ada potensi genangan terdeteksi untuk {argumen.kecamatan} dalam {argumen.hari} hari ke depan.")
        return

    print(f"Ditemukan {len(daftar_genangan)} periode potensi genangan di {argumen.kecamatan}:\n")
    for genangan in daftar_genangan:
        print(f"- Status: {genangan.tingkat_risiko.value.upper()}")
        print(f"  {intelligence_engine.buat_narasi(genangan)}")
        print()


if __name__ == "__main__":
    main()
