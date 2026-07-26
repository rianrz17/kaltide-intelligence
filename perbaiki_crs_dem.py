"""
Perbaiki tag CRS yang hilang pada file DEMNAS hasil download Ina-Geoportal.

Kenapa aman diasumsikan EPSG:4326: transform pixel size file ini adalah
0.000075 derajat/piksel, yang PERSIS sama dengan resolusi resmi DEMNAS
0.27 arcsecond (0.27/3600 = 0.000075). Ini konfirmasi kuat CRS aslinya
WGS84 geografis -- BUKAN tebakan sembarangan.

Jalankan: python perbaiki_crs_dem.py data/dem/dem_anggana.tif
"""
import sys
import rasterio
from rasterio.crs import CRS

path = sys.argv[1] if len(sys.argv) > 1 else "data/dem/dem_anggana.tif"

with rasterio.open(path, "r+") as src:
    if src.crs is not None:
        print(f"File sudah punya CRS: {src.crs}. Tidak diubah, cek manual dulu kalau perlu.")
    else:
        src.crs = CRS.from_epsg(4326)
        print(f"CRS berhasil di-set ke EPSG:4326 untuk {path}")

# Verifikasi ulang
with rasterio.open(path) as src:
    print("--- Verifikasi setelah perbaikan ---")
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
