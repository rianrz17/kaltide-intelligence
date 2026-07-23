"""
KALTIDE Intelligence - Backend API
====================================
Entry point utama aplikasi FastAPI. Menggabungkan seluruh router endpoint
(forecast, tide, flood, warning, impact, stations, analytics).

Jalankan dengan:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, flood, forecast, impact, stations, tide, warning
from app.core.config import dapatkan_pengaturan

pengaturan = dapatkan_pengaturan()

app = FastAPI(
    title="KALTIDE Intelligence API",
    description=(
        "API untuk prediksi risiko banjir rob di pesisir Kalimantan Timur, "
        "mengintegrasikan data cuaca, pasang surut, dan topografi."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=pengaturan.daftar_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router)
app.include_router(tide.router)
app.include_router(flood.router)
app.include_router(warning.router)
app.include_router(impact.router)
app.include_router(stations.router)
app.include_router(analytics.router)


@app.get("/", tags=["Root"])
def root() -> dict:
    """Endpoint dasar untuk memastikan API berjalan."""
    return {
        "layanan": "KALTIDE Intelligence API",
        "status": "aktif",
        "tahap": "Tahap 1 - Rule-Based + GIS",
        "dokumentasi": "/docs",
    }


@app.get("/health", tags=["Root"])
def health_check() -> dict:
    """Endpoint health-check untuk monitoring/uptime."""
    return {"status": "ok"}
