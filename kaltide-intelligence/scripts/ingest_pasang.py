"""
Script Ingest Data Pasang Surut
=================================
Mengambil data prediksi pasang surut untuk seluruh stasiun tide gauge aktif,
lalu menyimpannya ke tabel `tides` di database.

Jalankan secara manual:
    python scripts/ingest_pasang.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import text  # noqa: E402

from app.core.database import SesiLokal  # noqa: E402
from app.services.klien_pasang import KlienPasang  # noqa: E402


def ambil_daftar_tide_gauge(db) -> list[str]:
    """Mengambil daftar id stasiun bertipe tide_gauge yang aktif."""
    hasil = db.execute(
        text("SELECT id FROM stations WHERE aktif = true AND jenis = 'tide_gauge'")
    )
    return [baris[0] for baris in hasil]


def simpan_pasang(db, stasiun_id: str, data_pasang: list) -> None:
    """Menyimpan/update data pasang surut ke tabel `tides` (upsert sederhana)."""
    for item in data_pasang:
        db.execute(
            text(
                """
                INSERT INTO tides (station_id, waktu, tinggi_muka_air_m, jenis)
                VALUES (:station_id, :waktu, :tinggi_muka_air_m, :jenis)
                ON CONFLICT (station_id, waktu, jenis) DO UPDATE SET
                    tinggi_muka_air_m = EXCLUDED.tinggi_muka_air_m
                """
            ),
            {
                "station_id": stasiun_id,
                "waktu": item.waktu,
                "tinggi_muka_air_m": item.tinggi_muka_air_m,
                "jenis": item.jenis,
            },
        )
    db.commit()


def main() -> None:
    klien = KlienPasang()
    db = SesiLokal()

    try:
        daftar_stasiun = ambil_daftar_tide_gauge(db)
        print(f"Ditemukan {len(daftar_stasiun)} stasiun tide gauge aktif.")

        for stasiun_id in daftar_stasiun:
            try:
                data_pasang = klien.ambil_prediksi(stasiun_id, jumlah_hari=3)
                simpan_pasang(db, stasiun_id, data_pasang)
                print(f"[OK] {stasiun_id}: {len(data_pasang)} baris pasang surut disimpan.")
            except Exception as galat:  # noqa: BLE001
                print(f"[GAGAL] {stasiun_id}: {galat}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
