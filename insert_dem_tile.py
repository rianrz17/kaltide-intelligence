"""
Insert satu tile DEM ke tabel dem_tiles, dengan bbox dihitung otomatis
dari bounds file raster (bukan diketik manual -- menghindari salah ketik
koordinat).

Jalankan dari root project (folder kaltide-intelligence):
    python insert_dem_tile.py data/dem/dem_anggana_gabungan.tif "Anggana"
"""
import os
import sys

os.environ.pop("PROJ_LIB", None)
os.environ.pop("PROJ_DATA", None)

sys.path.insert(0, "backend")

import rasterio
from sqlalchemy import create_engine, text

from app.core.config import dapatkan_pengaturan

if len(sys.argv) != 3:
    raise SystemExit(
        "Pemakaian: python insert_dem_tile.py <path_relatif_ke_tif> <nama_tile>\n"
        "Contoh:    python insert_dem_tile.py data/dem/dem_anggana_gabungan.tif Anggana"
    )

path_file = sys.argv[1]
nama_tile = sys.argv[2]

with rasterio.open(path_file) as src:
    if src.crs is None:
        raise SystemExit(f"ERROR: {path_file} belum punya CRS! Jalankan perbaiki_crs_dem.py dulu.")
    bounds = src.bounds
    resolusi_m = src.res[0] * 111_000  # kasar: derajat -> meter di sekitar ekuator

pengaturan = dapatkan_pengaturan()
engine = create_engine(pengaturan.database_url)

with engine.begin() as conn:
    # Cek dulu apakah tile dengan nama sama sudah ada, supaya tidak dobel kalau script dijalankan ulang
    sudah_ada = conn.execute(
        text("SELECT id FROM dem_tiles WHERE nama_tile = :nama_tile"),
        {"nama_tile": nama_tile},
    ).fetchone()
    if sudah_ada:
        print(f"Tile '{nama_tile}' sudah ada di dem_tiles (id={sudah_ada.id}). Tidak insert ulang.")
        print("Kalau mau update, hapus dulu baris lama atau ganti nama_tile.")
        raise SystemExit(0)

    hasil = conn.execute(
        text(
            """
            INSERT INTO dem_tiles (nama_tile, path_file, resolusi_m, bbox)
            VALUES (
                :nama_tile,
                :path_file,
                :resolusi_m,
                ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326)
            )
            RETURNING id
            """
        ),
        {
            "nama_tile": nama_tile,
            "path_file": path_file,
            "resolusi_m": round(resolusi_m, 2),
            "xmin": bounds.left,
            "ymin": bounds.bottom,
            "xmax": bounds.right,
            "ymax": bounds.top,
        },
    ).fetchone()

    print(f"Berhasil insert dem_tiles id={hasil.id}")
    print(f"  nama_tile   : {nama_tile}")
    print(f"  path_file   : {path_file}")
    print(f"  resolusi_m  : {round(resolusi_m, 2)}")
    print(f"  bbox        : {bounds}")

    # Verifikasi langsung: cek apakah bbox ini beneran overlap dengan villages.geom Anggana
    overlap = conn.execute(
        text(
            """
            SELECT v.nama, v.kecamatan
            FROM villages v, dem_tiles dt
            WHERE dt.id = :dem_id AND ST_Intersects(dt.bbox, v.geom)
            """
        ),
        {"dem_id": hasil.id},
    ).fetchall()
    print(f"\nVerifikasi ST_Intersects -- village yang overlap dengan tile ini:")
    if overlap:
        for baris in overlap:
            print(f"  - {baris.nama} ({baris.kecamatan})")
    else:
        print("  (KOSONG -- tidak ada village yang overlap! Cek lagi bbox atau data villages.)")
