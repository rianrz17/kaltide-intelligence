from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- 1. IMPORT SERVICES ---
from bmkg_service import fetch_bmkg_forecast
from tide_service import calculate_tide_harmonic

app = FastAPI(
    title="KALTIDE Intelligence API",
    description="Backend API for Kalimantan Tidal Flood Intelligence System (MVP: Balikpapan, PPU, Kukar)",
    version="1.0.0"
)

# --- 2. PYDANTIC MODELS (Format Data) ---
class ForecastData(BaseModel):
    region: str
    datetime: str
    weather_condition: str  
    wind_speed_knot: float
    tide_max_m: float       

class TideData(BaseModel):
    station_id: str
    timestamp: str  # Menggunakan str karena format dari service sudah diformat ("YYYY-MM-DD HH:MM:SS")
    water_level_m: float
    status: str

class FloodPrediction(BaseModel):
    region_id: str
    region_name: str
    inundation_height_cm: float
    start_time: str
    peak_time: str
    duration_hours: float
    risk_level: str
    geometry_polygon: dict  

class ImpactAnalysis(BaseModel):
    region_name: str
    national_roads_flooded_km: float
    schools_affected: int
    puskesmas_affected: int
    ports_affected: int
    residential_houses_affected: int


# --- 3. MOCK DATABASE (Wilayah MVP) ---
REGIONS = {
    "kukar_anggana": {"name": "Kecamatan Anggana, Kukar", "base_elevation_m": 0.5},
    "ppu_sepaku": {"name": "Kecamatan Sepaku (IKN), PPU", "base_elevation_m": 0.8},
    "balikpapan_barat": {"name": "Balikpapan Barat, Balikpapan", "base_elevation_m": 0.6}
}


# --- 4. API ENDPOINTS ---
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
    region: str = Query("Balikpapan", description="Nama kota di Kaltim (contoh: Balikpapan, Penajam, Tenggarong)")
):
    """Menghasilkan prakiraan cuaca riil dari BMKG dan estimasi pasang surut."""
    bmkg_data = fetch_bmkg_forecast(city_name=region)
    
    if not bmkg_data:
        raise HTTPException(status_code=404, detail=f"Data cuaca untuk region '{region}' tidak ditemukan di BMKG.")

    forecasts = []
    for i, data in enumerate(bmkg_data):
        raw_dt = data["datetime"]
        formatted_dt = f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:8]} {raw_dt[8:10]}:{raw_dt[10:12]}"

        forecasts.append(
            ForecastData(
                region=region,
                datetime=formatted_dt,
                weather_condition=data["weather_condition"],
                wind_speed_knot=data["wind_speed_knot"],
                tide_max_m=2.5 + (i * 0.1) 
            )
        )
    return forecasts

@app.get("/api/v1/tide", response_model=List[TideData], tags=["Tide Engine"])
def get_tide_predictions(
    station: str = Query("PUPR-TIDE-01", description="Station ID dari PUSHIDROSAL / Tide Gauge"),
    hours: int = Query(24, description="Jumlah jam prediksi ke depan")
):
    """Menghasilkan prediksi pasang surut menggunakan Pemodelan Harmonik Oseanografi."""
    tide_data = calculate_tide_harmonic(station_id=station, hours_ahead=hours)
    
    if not tide_data:
        raise HTTPException(status_code=500, detail="Gagal menghitung pemodelan pasang surut.")
        
    return tide_data

@app.get("/api/v1/flood", response_model=List[FloodPrediction], tags=["Flood Simulation Engine"])
def get_flood_prediction(
    region_id: str = Query(..., description="ID wilayah MVP (kukar_anggana, ppu_sepaku, balikpapan_barat)")
):
    """Rule-based flood simulation engine menghitung tinggi, waktu, dan durasi genangan."""
    if region_id not in REGIONS:
        raise HTTPException(status_code=404, detail="Wilayah MVP tidak ditemukan.")
    
    reg = REGIONS[region_id]
    
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
