"""
Gabungkan (mosaic) beberapa tile DEMNAS yang bersebelahan jadi satu file,
supaya dem_tiles cuma perlu 1 baris per wilayah -- menghindari ambiguitas
LIMIT 1 di SpatialFloodEngine.cari_tile_dem() kalau ada lebih dari satu
tile yang overlap dengan geom village yang sama.

Jalankan:
    python mosaic_dem.py dem_anggana.tif dem_anggana_timur.tif -o dem_anggana_gabungan.tif

(jalankan dari root project, path relatif ke data/dem/ ditambahkan otomatis)
"""
import argparse
from pathlib import Path

import rasterio
from rasterio.merge import merge

parser = argparse.ArgumentParser()
parser.add_argument("tiles", nargs="+", help="Nama file tile di dalam data/dem/")
parser.add_argument("-o", "--output", required=True, help="Nama file hasil gabungan")
args = parser.parse_args()

folder = Path("data/dem")
sumber = [rasterio.open(folder / t) for t in args.tiles]

for src, nama in zip(sumber, args.tiles):
    if src.crs is None:
        raise SystemExit(
            f"ERROR: {nama} belum punya CRS! Jalankan perbaiki_crs_dem.py dulu untuk file ini."
        )

mosaic, transform_gabungan = merge(sumber)

meta = sumber[0].meta.copy()
meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": transform_gabungan,
})

output_path = folder / args.output
with rasterio.open(output_path, "w", **meta) as dst:
    dst.write(mosaic)

for src in sumber:
    src.close()

# Verifikasi hasil gabungan
with rasterio.open(output_path) as hasil:
    print(f"Berhasil digabung ke: {output_path}")
    print("CRS:", hasil.crs)
    print("Bounds:", hasil.bounds)
    print("Ukuran:", hasil.width, "x", hasil.height)
