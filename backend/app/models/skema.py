"""
Skema Data (Pydantic)
======================
Mendefinisikan struktur data yang dipakai untuk request & response API,
serta struktur internal yang dipertukarkan antar-engine.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TingkatRisiko(str, Enum):
    """Klasifikasi status peringatan dini rob."""

    AMAN = "aman"          # 🟢
    WASPADA = "waspada"    # 🟡
    SIAGA = "siaga"        # 🟠
    AWAS = "awas"          # 🔴


class TitikKoordinat(BaseModel):
    """Representasi satu titik koordinat geografis."""

    lat: float = Field(..., description="Lintang (latitude)")
    lon: float = Field(..., description="Bujur (longitude)")


class DataPasang(BaseModel):
    """Data prediksi pasang surut pada satu stasiun/waktu tertentu."""

    stasiun_id: str
    waktu: datetime
    tinggi_muka_air_m: float = Field(..., description="Tinggi muka air laut dalam meter")
    jenis: str = Field(default="prediksi", description="prediksi atau observasi")


class DataCuaca(BaseModel):
    """Ringkasan parameter cuaca hasil forecast BMKG."""

    stasiun_id: str
    waktu: datetime
    curah_hujan_mm: float = 0.0
    kecepatan_angin_ms: float | None = None
    arah_angin_derajat: float | None = None
    tekanan_udara_hpa: float | None = None


class PermintaanForecast(BaseModel):
    """Parameter permintaan forecast cuaca & pasang."""

    wilayah: str = Field(..., description="Nama wilayah/kecamatan, contoh: Anggana")
    jumlah_hari: int = Field(default=3, ge=1, le=7)


class GenanganWilayah(BaseModel):
    """Hasil simulasi genangan pada satu wilayah/kecamatan."""

    wilayah: str
    kecamatan: str
    tinggi_genangan_min_cm: float
    tinggi_genangan_max_cm: float
    waktu_mulai: datetime
    waktu_puncak: datetime
    durasi_jam: float
    tingkat_risiko: TingkatRisiko
    luas_genangan_ha: float | None = None
    volume_genangan_m3: float | None = None
    tinggi_pasang_m: float | None = Field(
        default=None,
        description=(
            "Tinggi pasang mentah (meter) yang dipakai menghitung genangan ini. "
            "Dibutuhkan SpatialFloodEngine (Tahap 2) untuk hitung water level; "
            "None berarti data lama / sebelum field ini ditambahkan."
        ),
    )


class DampakInfrastruktur(BaseModel):
    """Ringkasan dampak genangan terhadap infrastruktur di suatu wilayah."""

    wilayah: str
    jalan_terdampak_km: float = 0.0
    sekolah_terdampak: int = 0
    puskesmas_terdampak: int = 0
    pelabuhan_terdampak: int = 0
    rumah_terdampak: int = 0
    narasi: str = Field(
        default="",
        description="Ringkasan naratif dampak, contoh keluaran Intelligence Engine",
    )


class PeringatanDini(BaseModel):
    """Struktur data peringatan dini yang dikirim ke pengguna/kanal notifikasi."""

    wilayah: str
    tingkat_risiko: TingkatRisiko
    pesan: str
    waktu_terbit: datetime
    berlaku_hingga: datetime
