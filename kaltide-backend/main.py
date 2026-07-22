from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI(
    title="KALTIDE Intelligence API",
    description="Backend API for Kalimantan Tidal Flood Intelligence System (MVP: Balikpapan, PPU, Kukar)",
    version="1.0.0"
)

# --- Pydantic Models ---

class TideData(item=BaseModel):
    station_id: str
    station_name: str
    timestamp: datetime
    water_level_m: float
    status: str

class ForecastData(BaseModel):
    region: str
    date: str
    rainfall_mm: float
    wind_speed_knot: float
    tide_max_m: float

class FloodPrediction(BaseModel):
    region_id: str
    region_name: str
    inundation_height_cm: float
    start_time: str
    peak_time: str
    duration_hours: float
    risk_level: str
    geometry_polygon: dict  # GeoJSON format placeholder

class ImpactAnalysis(BaseModel):
    region_name: str
    national_roads_flooded_km: float
    schools_affected: int
    puskesmas_affected: int
    ports_affected: int
    residential_houses_affected: int

# --- Mock Database / Service Layer (Placeholder for PostGIS integration) ---

REGIONS = {
    "kukar_anggana": {"name": "Kecamatan Anggana, Kukar", "base_elevation_m": 0.5},
    "ppu_sepaku": {"name": "Kecamatan Sepaku (IKN), PPU", "base_elevation_m": 0.8},
    "balikpapan_barat": {"name": "Balikpapan Barat, Balikpapan", "base_elevation_m": 0.6}
}

# --- API Endpoints ---

@app.get("/", tags=["System"])
def root():
    return {
        "system": "KALTIDE Intelligence API",
        "status": "Operational",
        "mvp_coverage": ["Balikpapan", "Penajam Paser Utara", "Kutai Kartanegara"],
        "version": "1.0.0"
    }

@app.get("/api/v1/forecast", response_model=List[ForecastData], tags=["Forecast Engine"])
def get_forecast(
    region: Optional[str] = Query(None, description="Filter by region key (e.g., kukar_anggana)")
):
    """Menghasilkan prakiraan parameter meteorologi dan pasang surut 1-7 hari."""
    forecasts = [
        ForecastData(
            region="Kecamatan Anggana, Kukar",
            date=(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
            rainfall_mm=25.5 + (i * 2.1),
            wind_speed_knot=12.0,
            tide_max_m=2.8 + (i * 0.1)
        ) for i in range(3)
    ]
    if region:
        matched = [f for f in forecasts if region.lower() in f.region.lower()]
        return matched
    return forecasts

@app.get("/api/v1/tide", response_model=List[TideData], tags=["Tide Engine"])
def get_tide_predictions(
    station: Optional[str] = Query("PUPR-TIDE-01", description="Station ID dari PUSHIDROSAL / Tide Gauge")
):
    """Menampilkan data pasang surut air laut real-time dan prediksi harian."""
    now = datetime.now()
    return [
        TideData(
            station_id=station,
            station_name="Stasiun Pasang Surut Teluk Balikpapan",
            timestamp=now,
            water_level_m=2.65,
            status="Pasang Tinggi (High Tide)"
        )
    ]

@app.get("/api/v1/flood", response_model=List[FloodPrediction], tags=["Flood Simulation Engine"])
def get_flood_prediction(
    region_id: str = Query(..., description="ID wilayah MVP (kukar_anggana, ppu_sepaku, balikpapan_barat)")
):
    """Rule-based flood simulation engine menghitung tinggi, waktu, dan durasi genangan."""
    if region_id not in REGIONS:
        raise HTTPException(status_code=404, detail="Wilayah MVP tidak ditemukan.")
    
    reg = REGIONS[region_id]
    
    # Logika rule-based sederhana untuk MVP (Elevasi DEM vs Pasang + Hujan)
    simulated_height = 45.0  # cm
    risk = "Siaga" if simulated_height > 40 else "Waspada"

    return [
        FloodPrediction(
            region_id=region_id,
            region_name=reg["name"],
            inundation_height_cm=simulated_height,
            start_time="03:00 WITA",
            peak_time="05:30 WITA",
            duration_hours=4.5,
            risk_level=risk,
            geometry_polygon={
                "type": "Polygon",
                "coordinates": [[[117.2, -0.5], [117.3, -0.5], [117.3, -0.6], [117.2, -0.6], [117.2, -0.5]]]
            }
        )
    ]

@app.get("/api/v1/warning", tags=["Early Warning"])
def get_early_warning():
    """Mengembalikan status peringatan dini aktif berdasarkan tingkat risiko wilayah MVP."""
    return {
        "timestamp": datetime.now().isoformat(),
        "active_warnings": [
            {
                "region": "Kecamatan Anggana, Kukar",
                "level": "Oranye",
                "status": "Siaga",
                "message": "Potensi rob 35-60 cm pada pukul 03.00-07.00 WITA. Waspadai akses jalan pelabuhan."
            },
            {
                "region": "Kecamatan Sepaku, PPU",
                "level": "Kuning",
                "status": "Waspada",
                "message": "Genangan ringan di area pesisir sungai sekunder."
            }
        ]
    }

@app.get("/api/v1/impact", response_model=ImpactAnalysis, tags=["Intelligence Engine"])
def get_impact_analysis(
    region_name: str = Query("Kecamatan Anggana, Kukar")
):
    """Menghitung estimasi dampak infrastruktur secara spasial."""
    return ImpactAnalysis(
        region_name=region_name,
        national_roads_flooded_km=2.3,
        schools_affected=12,
        puskesmas_affected=3,
        ports_affected=2,
        residential_houses_affected=1200
    )
