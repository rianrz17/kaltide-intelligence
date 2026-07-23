"""
Koneksi Database
=================
Menyiapkan engine SQLAlchemy dan session database (PostgreSQL + PostGIS)
yang digunakan oleh seluruh endpoint dan engine prediksi.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import dapatkan_pengaturan

pengaturan = dapatkan_pengaturan()

engine = create_engine(pengaturan.database_url, pool_pre_ping=True)

SesiLokal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Basis(DeclarativeBase):
    """Base class untuk seluruh model ORM SQLAlchemy."""


def dapatkan_db() -> Generator[Session, None, None]:
    """Dependency FastAPI untuk mendapatkan sesi database per-request."""
    db = SesiLokal()
    try:
        yield db
    finally:
        db.close()
