"""
Konfigurasi Aplikasi
=====================
Modul ini membaca variabel lingkungan (.env) dan menyediakannya sebagai
objek konfigurasi yang bisa dipakai di seluruh aplikasi backend.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Pengaturan(BaseSettings):
    """Kumpulan pengaturan aplikasi yang diambil dari environment variable."""

    # Database
    database_url: str = "postgresql://kaltide:kaltide@localhost:5432/kaltide"

    # BMKG API
    bmkg_api_base_url: str = "https://api.bmkg.go.id"
    bmkg_api_key: str = ""

    # Tide / PUSHIDROSAL
    tide_api_base_url: str = ""
    tide_api_key: str = ""

    # Aplikasi umum
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "ubah-kunci-ini"
    cors_origins: str = "http://localhost:3000"

    # Bounding box wilayah MVP: Balikpapan, PPU (IKN), Kukar (Muara Jawa-Anggana)
    mvp_bbox: str = "116.6,-1.35,117.3,-0.4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def daftar_cors_origins(self) -> list[str]:
        """Mengubah string CORS_ORIGINS menjadi list, dipisahkan koma."""
        return [asal.strip() for asal in self.cors_origins.split(",") if asal.strip()]

    @property
    def bbox_mvp(self) -> tuple[float, float, float, float]:
        """Mengembalikan bounding box MVP sebagai tuple (min_lon, min_lat, max_lon, max_lat)."""
        nilai = [float(x) for x in self.mvp_bbox.split(",")]
        return nilai[0], nilai[1], nilai[2], nilai[3]


@lru_cache
def dapatkan_pengaturan() -> Pengaturan:
    """Mengambil instance Pengaturan (di-cache agar tidak dibaca berulang kali)."""
    return Pengaturan()
