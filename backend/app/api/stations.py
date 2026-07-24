"""Endpoint daftar stasiun observasi (AWS, ARG, tide gauge)."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/stations", tags=["Stations"])


class Stasiun(BaseModel):
    """Metadata satu stasiun observasi."""

    id: str
    nama: str
    jenis: str  # aws | arg | tide_gauge | radar
    lat: float
    lon: float
    kecamatan: str


# TODO: pindahkan ke tabel `stations` di database (lihat database/schema.sql)
# setelah proses ingest data stasiun MVP selesai. Koordinat di sini disamakan
# persis dengan koordinat kecamatan di seed_mvp.sql/seed_ekspansi.sql supaya
# query spasial (/flood, /impact) konsisten.
DAFTAR_STASIUN_CONTOH = [
    Stasiun(id="anggana-01", nama="AWS Anggana", jenis="aws", lat=-0.478, lon=117.240, kecamatan="Anggana"),
    Stasiun(id="balikpapan-01", nama="Tide Gauge Balikpapan", jenis="tide_gauge", lat=-1.267, lon=116.831, kecamatan="Balikpapan Kota"),
    Stasiun(id="ppu-01", nama="AWS Penajam", jenis="aws", lat=-1.246, lon=116.744, kecamatan="Penajam"),
    Stasiun(id="samarinda-01", nama="AWS Samarinda Ilir", jenis="aws", lat=-0.495, lon=117.162, kecamatan="Samarinda Ilir"),
    Stasiun(id="bontang-01", nama="Tide Gauge Bontang Utara", jenis="tide_gauge", lat=0.152, lon=117.485, kecamatan="Bontang Utara"),
    Stasiun(id="berau-01", nama="AWS Tanjung Redeb", jenis="aws", lat=2.152, lon=117.502, kecamatan="Tanjung Redeb"),
]


@router.get("/", response_model=list[Stasiun])
def daftar_stasiun() -> list[Stasiun]:
    """Mengembalikan daftar stasiun observasi yang tersedia (data contoh, Tahap 1)."""
    return DAFTAR_STASIUN_CONTOH
