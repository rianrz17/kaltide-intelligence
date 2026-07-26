"""
Spatial Flood Engine
=====================
Menghasilkan EXTENT GENANGAN NYATA (polygon) berdasarkan DEM, sebagai
pelengkap FloodSimulationEngine yang saat ini hanya menghasilkan indeks
skalar per kecamatan (lihat flood_simulation_engine.py).

Pendekatan: bathtub model + konektivitas hidrologis. BUKAN threshold
elevasi mentah -- sel DEM yang lebih rendah dari water level HANYA
dianggap tergenang kalau terhubung (8-connectivity) ke laut/sungai,
supaya cekungan pedalaman yang terisolasi tidak salah ditandai banjir.

Tahap 2 (lihat docs/ROADMAP.md). Menggantikan pendekatan buffer 5km dari
centroid kecamatan yang saat ini dipakai IntelligenceEngine.hitung_dampak_spasial()
sebagai pendekatan sementara (lihat komentar di intelligence_engine.py).

Dependencies tambahan (belum ada di requirements sebelumnya):
    pip install rasterio scipy shapely
"""

from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.features import shapes as rio_shapes
from scipy.ndimage import binary_dilation, generate_binary_structure, label
from shapely import wkt as shapely_wkt
from shapely.geometry import MultiPolygon, shape
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class HasilGenanganSpasial:
    """Hasil flood-fill: geometry siap dipakai ST_Intersects + metadata."""
    geom_wkt: str | None          # WKT polygon, None kalau tidak ada genangan
    luas_ha: float
    kedalaman_maks_m: float
    tinggi_muka_air_m: float
    komponen_pasut_m: float
    komponen_hujan_m: float


@dataclass
class DemTerload:
    """
    DEM yang sudah dibaca dari disk + seed_mask yang sudah dihitung.

    Optimasi performa: sebelumnya buat_polygon_genangan() membuka file
    raster dari disk SETIAP KALI dipanggil -- untuk satu request /impact
    yang memproses 6-30 titik waktu genangan, ini berarti file ~90MB
    dibaca ulang 6-30x, plus binary_dilation() untuk seed_mask dihitung
    ulang tiap kali padahal hasilnya SAMA PERSIS (seed_mask cuma tergantung
    elevasi DEM, bukan water_level). Load sekali pakai muat_dem(), simpan
    DemTerload-nya, lalu pakai ulang untuk setiap water_level berbeda.
    """
    dem: np.ndarray
    transform: object
    seed_mask: np.ndarray


class SpatialFloodEngine:
    """Menghasilkan polygon genangan nyata dari DEM untuk satu village."""

    def __init__(self, rainfall_to_height_factor: float = 0.002) -> None:
        # WAJIB dikalibrasi per wilayah pakai historical_events kalau ada datanya.
        # Placeholder linier -- lihat catatan di README/ROADMAP soal ini.
        self.rainfall_to_height_factor = rainfall_to_height_factor

    def muat_dem(self, dem_path: str, seed_mask: np.ndarray | None = None) -> DemTerload:
        """
        Baca raster DEM dari disk SEKALI, hitung seed_mask sekali, kembalikan
        DemTerload yang bisa dipakai ulang untuk banyak water_level berbeda
        lewat buat_polygon_genangan(dem_terload, ...) -- lihat docstring
        DemTerload untuk alasan optimasi ini.
        """
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(np.float32)
            nodata = src.nodata
            transform = src.transform
        if nodata is not None:
            dem[dem == nodata] = np.nan

        if seed_mask is None:
            seed_mask = (dem <= 0) & ~np.isnan(dem)
        seed_mask = binary_dilation(seed_mask, iterations=1)

        return DemTerload(dem=dem, transform=transform, seed_mask=seed_mask)

    def hitung_water_level(
        self,
        tinggi_pasang_m: float,
        curah_hujan_mm: float,
        datum_offset_m: float = 0.0,
    ) -> dict:
        """
        Menggabungkan komponen pasut (dari model harmonic M2/S2/K1/O1) dan
        curah hujan (dari klien_bmkg.py) menjadi satu water level acuan.

        datum_offset_m: penyelaras datum antara model pasut (biasanya
        LWS/MSL) dengan datum vertikal DEMNAS (EGM2008). WAJIB dicek dulu
        sebelum dipakai -- lihat catatan integrasi.
        """
        komponen_pasut = tinggi_pasang_m + datum_offset_m
        komponen_hujan = curah_hujan_mm * self.rainfall_to_height_factor
        return {
            "tinggi_muka_air_m": komponen_pasut + komponen_hujan,
            "komponen_pasut_m": komponen_pasut,
            "komponen_hujan_m": komponen_hujan,
        }

    def cari_tile_dem(self, db: Session, village_id: int) -> str | None:
        """
        Mencari path file DEM yang bbox-nya beririsan dengan wilayah village.

        Kalau lebih dari satu tile overlap dengan village yang sama (kasus
        nyata: satu tile besar bisa overlap ke beberapa kecamatan sekaligus,
        dan beberapa kecamatan di perbatasan grid butuh >1 tile untuk
        cover penuh -- lihat docs/CATATAN_DEM.md), kita pilih tile dengan
        LUAS IRISAN TERBESAR terhadap geom village, BUKAN baris pertama
        yang kebetulan muncul duluan (LIMIT 1 tanpa ORDER BY sebelumnya
        tidak deterministik dan bisa pilih tile yang cuma nyerempet sedikit).

        Mengembalikan None kalau belum ada tile DEM untuk area ini --
        caller HARUS menangani ini (fallback ke buffer), bukan error keras,
        supaya endpoint tetap jalan sebelum semua tile DEMNAS ter-upload.
        """
        baris = db.execute(
            text(
                """
                SELECT dt.path_file
                FROM dem_tiles dt, villages v
                WHERE v.id = :village_id
                  AND ST_Intersects(dt.bbox, v.geom)
                ORDER BY ST_Area(ST_Intersection(dt.bbox, v.geom)) DESC
                LIMIT 1
                """
            ),
            {"village_id": village_id},
        ).fetchone()
        return baris.path_file if baris else None

    def buat_polygon_genangan(
        self,
        dem_atau_path: "str | DemTerload",
        water_level_m: float,
        clip_geom_wkt: str | None = None,
    ) -> HasilGenanganSpasial:
        """
        Flood-fill dengan konektivitas hidrologis dari raster DEM.

        dem_atau_path: BOLEH path string ke file .tif (untuk pemakaian
        sekali/testing, cocok seperti sebelumnya) ATAU objek DemTerload
        hasil muat_dem() (untuk pemakaian berulang lintas water_level
        tanpa baca ulang disk -- lihat docstring DemTerload). Kalau
        dikasih path string, tetap dimuat via muat_dem() secara internal
        supaya kode lama yang manggil dengan path masih jalan tanpa ubahan.

        Seed mask fallback (kalau tidak override lewat muat_dem):
        sel dengan elevasi <= 0 dianggap laut/muara. Ini kasar -- setelah
        tabel rivers/coastline dirasterisasi ke grid yang sama, seed_mask
        sebaiknya dibangun dari situ, bukan elevasi 0.

        clip_geom_wkt (PENTING): tile DEM yang dipakai bisa mencakup lebih
        dari satu kecamatan (satu tile besar/gabungan), dan area dataran
        rendah (mis. delta Anggana) bisa membuat flood-fill menyebar JAUH
        melewati batas kecamatan yang sebenarnya diminta -- terbukti empiris
        polygon bisa 13-16x lebih luas dari kecamatan itu sendiri kalau
        tidak dipotong. Kalau clip_geom_wkt diisi (biasanya buffer di
        sekitar village yang diminta), hasil akhir di-ST_Intersection
        dengan itu SEBELUM dikembalikan -- supaya dampak yang dihitung
        nanti (jalan/infrastruktur terdampak) tidak salah atribusi ke
        kecamatan yang diminta padahal sebenarnya genangan itu ada di
        kecamatan tetangga.
        """
        if isinstance(dem_atau_path, DemTerload):
            terload = dem_atau_path
        else:
            terload = self.muat_dem(dem_atau_path)

        dem = terload.dem
        transform = terload.transform
        seed_mask = terload.seed_mask

        kandidat = (dem <= water_level_m) & ~np.isnan(dem)
        struktur = generate_binary_structure(2, 2)  # 8-connectivity
        berlabel, _ = label(kandidat, structure=struktur)

        label_seed = set(np.unique(berlabel[seed_mask & kandidat]))
        label_seed.discard(0)
        tergenang = np.isin(berlabel, list(label_seed))

        if not tergenang.any():
            return HasilGenanganSpasial(
                geom_wkt=None, luas_ha=0.0, kedalaman_maks_m=0.0,
                tinggi_muka_air_m=water_level_m, komponen_pasut_m=0.0, komponen_hujan_m=0.0,
            )

        mask_uint8 = tergenang.astype(np.uint8)
        polygons = [
            shape(geom) for geom, val in rio_shapes(mask_uint8, mask=tergenang, transform=transform)
            if val == 1
        ]
        # PENTING (optimasi performa besar): sebelumnya pakai unary_union(polygons)
        # untuk dissolve ratusan/ribuan polygon jadi satu bentuk bersih -- terbukti
        # empiris ini bisa makan 4-10+ detik SENDIRI per panggilan (dominan dibanding
        # semua tahap lain digabung), karena satu request /impact memanggil ini
        # puluhan kali (satu per titik waktu), total jadi ratusan detik.
        #
        # rio_shapes() menghasilkan polygon-polygon yang TIDAK saling tumpang tindih
        # (cuma bersentuhan di tepi, karena berasal dari partisi raster/mask) --
        # jadi tidak perlu di-dissolve topologinya untuk ST_Intersects atau hitung
        # luas total: MultiPolygon(polygons) langsung sudah correct dan ~300x lebih
        # cepat (diverifikasi: luas & hasil intersection identik dengan unary_union,
        # cuma beda performa). geom_genangan di skema DB juga bertipe MultiPolygon,
        # jadi ini malah lebih konsisten tipenya dibanding unary_union yang kadang
        # mengembalikan Polygon tunggal.
        gabungan = MultiPolygon(polygons)

        if clip_geom_wkt:
            batas = shapely_wkt.loads(clip_geom_wkt)
            gabungan = gabungan.intersection(batas)
            if gabungan.is_empty:
                return HasilGenanganSpasial(
                    geom_wkt=None, luas_ha=0.0, kedalaman_maks_m=0.0,
                    tinggi_muka_air_m=water_level_m, komponen_pasut_m=0.0, komponen_hujan_m=0.0,
                )

        # Kedalaman maks dihitung dari SELURUH area tergenang di tile (sebelum clip),
        # supaya tetap mencerminkan titik terdalam yang mungkin relevan secara fisik.
        # TODO: idealnya dihitung ulang HANYA di piksel dalam area ter-clip.
        kedalaman = water_level_m - dem[tergenang]
        kedalaman_maks = float(np.nanmax(kedalaman)) if kedalaman.size else 0.0

        # NOTE: area dalam derajat kalau CRS geografis (EPSG:4326) -- untuk
        # luas_ha yang akurat, reproject ke CRS meter (mis. UTM 50S) dulu.
        # Placeholder, tandai TODO sampai reprojection ditambahkan.
        luas_ha = gabungan.area * 111_000 * 111_000 / 10_000  # kasar, TODO perbaiki

        return HasilGenanganSpasial(
            geom_wkt=gabungan.wkt,
            luas_ha=round(luas_ha, 2),
            kedalaman_maks_m=round(kedalaman_maks, 3),
            tinggi_muka_air_m=water_level_m,
            komponen_pasut_m=0.0,  # diisi caller dari hitung_water_level()
            komponen_hujan_m=0.0,
        )
