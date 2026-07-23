"""
Script Muat Data OSM ke Database
===================================
Membaca file GeoJSON hasil ekspor dari Overpass Turbo (lihat
docs/SUMBER_DATA_INFRASTRUKTUR.md untuk cara mendapatkannya) dan mengisi
tabel `infrastructure` (titik: sekolah, puskesmas, pelabuhan) serta
`roads` (garis: jalan) di PostGIS.

Cara pakai:
    python scripts/muat_data_osm.py \
        --infrastruktur data/raw/infrastruktur_osm.geojson \
        --jalan data/raw/jalan_osm.geojson
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import text  # noqa: E402

from app.core.database import SesiLokal  # noqa: E402

# Pemetaan tag OSM -> kategori jenis infrastruktur di skema kita
PEMETAAN_JENIS = {
    "school": "sekolah",
    "hospital": "puskesmas",
    "clinic": "puskesmas",
    "ferry_terminal": "pelabuhan",
}


def klasifikasi_jenis(properti: dict) -> str | None:
    """Menentukan kategori jenis infrastruktur dari tag OSM (amenity/healthcare/harbour)."""
    amenity = properti.get("amenity")
    if amenity in PEMETAAN_JENIS:
        return PEMETAAN_JENIS[amenity]
    if properti.get("healthcare") == "center":
        return "puskesmas"
    if properti.get("harbour") == "yes":
        return "pelabuhan"
    return None


def muat_infrastruktur(db, path_geojson: str) -> int:
    """Memuat titik infrastruktur (node) dari GeoJSON ke tabel `infrastructure`."""
    with open(path_geojson, encoding="utf-8") as berkas:
        data = json.load(berkas)

    jumlah_masuk = 0
    for fitur in data.get("features", []):
        geometri = fitur.get("geometry", {})
        if geometri.get("type") != "Point":
            continue  # hanya proses titik; garis jalan ditangani muat_jalan()

        properti = fitur.get("properties", {}) or fitur.get("tags", {})
        jenis = klasifikasi_jenis(properti)
        if jenis is None:
            continue

        nama = properti.get("name", f"{jenis.capitalize()} (tanpa nama di OSM)")
        lon, lat = geometri["coordinates"]

        db.execute(
            text(
                """
                INSERT INTO infrastructure (nama, jenis, geom)
                VALUES (:nama, :jenis, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                """
            ),
            {"nama": nama, "jenis": jenis, "lon": lon, "lat": lat},
        )
        jumlah_masuk += 1

    db.commit()
    return jumlah_masuk


def muat_jalan(db, path_geojson: str) -> int:
    """Memuat ruas jalan (LineString) dari GeoJSON ke tabel `roads`."""
    with open(path_geojson, encoding="utf-8") as berkas:
        data = json.load(berkas)

    jumlah_masuk = 0
    for fitur in data.get("features", []):
        geometri = fitur.get("geometry", {})
        if geometri.get("type") not in ("LineString", "MultiLineString"):
            continue

        properti = fitur.get("properties", {}) or fitur.get("tags", {})
        nama = properti.get("name", "Jalan tanpa nama")
        kelas = properti.get("highway", "tidak diketahui")

        # Bungkus jadi WKT sederhana; untuk MultiLineString, PostGIS ST_GeomFromGeoJSON
        # menangani otomatis asalkan tipe di GeoJSON konsisten.
        geojson_geometri = json.dumps(geometri)

        db.execute(
            text(
                """
                INSERT INTO roads (nama, kelas, geom)
                VALUES (
                    :nama, :kelas,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326))
                )
                """
            ),
            {"nama": nama, "kelas": kelas, "geojson": geojson_geometri},
        )
        jumlah_masuk += 1

    db.commit()
    return jumlah_masuk


def main() -> None:
    parser = argparse.ArgumentParser(description="Muat data GeoJSON OSM (Overpass Turbo) ke database KALTIDE.")
    parser.add_argument("--infrastruktur", help="Path file GeoJSON titik infrastruktur (sekolah/puskesmas/pelabuhan)")
    parser.add_argument("--jalan", help="Path file GeoJSON garis jalan (highway)")
    argumen = parser.parse_args()

    if not argumen.infrastruktur and not argumen.jalan:
        print("Beri minimal salah satu: --infrastruktur atau --jalan")
        return

    db = SesiLokal()
    try:
        if argumen.infrastruktur:
            jumlah = muat_infrastruktur(db, argumen.infrastruktur)
            print(f"[OK] {jumlah} titik infrastruktur dimuat dari {argumen.infrastruktur}")

        if argumen.jalan:
            jumlah = muat_jalan(db, argumen.jalan)
            print(f"[OK] {jumlah} ruas jalan dimuat dari {argumen.jalan}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
