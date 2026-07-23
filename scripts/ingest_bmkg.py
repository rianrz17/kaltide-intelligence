"""
Script Ingest Data BMKG
=======================
Mengambil data prakiraan cuaca dari BMKG untuk seluruh stasiun aktif,
lalu menyimpannya ke tabel `forecast` di database.

Jalankan secara manual:
    python scripts/ingest_bmkg.py

Atau jadwalkan berkala (mis. tiap 6 jam) via cron/APScheduler.
"""

import sys
from pathlib import Path

# Agar bisa mengimpor modul dari backend/app saat script dijalankan langsung
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import text  # noqa: E402

from app.core.database import SesiLokal  # noqa: E402
from app.services.klien_bmkg import KlienBMKG  # noqa: E402


def ambil_daftar_stasiun_aktif(db) -> list[str]:
    """Mengambil daftar id stasiun aktif dari tabel `stations`."""
    hasil = db.execute(text("SELECT id FROM stations WHERE aktif = true"))
    return [baris[0] for baris in hasil]


def simpan_forecast(db, stasiun_id: str, data_cuaca: list) -> None:
    """Menyimpan/update data cuaca ke tabel `forecast` (upsert sederhana)."""
    for item in data_cuaca:
        db.execute(
            text(
                """
                INSERT INTO forecast
                    (station_id, waktu, curah_hujan_mm, kecepatan_angin_ms, arah_angin_derajat, tekanan_udara_hpa)
                VALUES
                    (:station_id, :waktu, :curah_hujan_mm, :kecepatan_angin_ms, :arah_angin_derajat, :tekanan_udara_hpa)
                ON CONFLICT (station_id, waktu) DO UPDATE SET
                    curah_hujan_mm = EXCLUDED.curah_hujan_mm,
                    kecepatan_angin_ms = EXCLUDED.kecepatan_angin_ms,
                    arah_angin_derajat = EXCLUDED.arah_angin_derajat,
                    tekanan_udara_hpa = EXCLUDED.tekanan_udara_hpa
                """
            ),
            {
                "station_id": stasiun_id,
                "waktu": item.waktu,
                "curah_hujan_mm": item.curah_hujan_mm,
                "kecepatan_angin_ms": item.kecepatan_angin_ms,
                "arah_angin_derajat": item.arah_angin_derajat,
                "tekanan_udara_hpa": item.tekanan_udara_hpa,
            },
        )
    db.commit()


def main() -> None:
    klien = KlienBMKG()
    db = SesiLokal()

    try:
        daftar_stasiun = ambil_daftar_stasiun_aktif(db)
        print(f"Ditemukan {len(daftar_stasiun)} stasiun aktif.")

        for stasiun_id in daftar_stasiun:
            try:
                data_cuaca = klien.ambil_forecast(stasiun_id, jumlah_hari=3)
                simpan_forecast(db, stasiun_id, data_cuaca)
                print(f"[OK] {stasiun_id}: {len(data_cuaca)} baris forecast disimpan.")
            except Exception as galat:  # noqa: BLE001
                print(f"[GAGAL] {stasiun_id}: {galat}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
