from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import BuoyTelemetryIn, CitizenReportIn, UnifiedDiagnosisOut
from app.services.alert_engine import compute_unified_diagnosis
from app.services.nasa_service import NasaSatelliteService
from app.services.weather_service import MeteomaticsService
from fastapi.responses import FileResponse


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend de vigilancia hídrica, detección de tendencias NASA (p < 0.05), alerta temprana de inundaciones y mitigación circular con Biochar.",
)

@app.get("/", include_in_schema=False)
def serve_frontend():
  return FileResponse("index.html") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

nasa_service = NasaSatelliteService()
weather_service = MeteomaticsService()

TELEMETRY_STORE: List[BuoyTelemetryIn] = []
CITIZEN_REPORTS_STORE: List[CitizenReportIn] = []

@app.get("/")
def root():
    return {
        "proyecto": "EcoStream Sgo API",
        "estado": "Activo",
        "documentacion": "http://127.0.0.1:8000/docs",
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "coordinates": [settings.TARGET_LAT, settings.TARGET_LON]}


@app.get("/api/v1/satellite/trends")
async def get_nasa_trends(lat: float = settings.TARGET_LAT, lon: float = settings.TARGET_LON):
    try:
        trends = await nasa_service.analyze_all_satellite_trends(lat, lon)
        pc_scenes = nasa_service.query_planetary_computer_scenes(lat, lon)
        return {
            "coordinates": {"lat": lat, "lon": lon},
            "period": f"{settings.START_DATE} - {settings.END_DATE}",
            "planetary_computer": pc_scenes,
            "trends": trends,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error procesando datos satelitales: {exc}")


@app.post("/api/v1/iot/telemetry", response_model=BuoyTelemetryIn)
def ingest_buoy_telemetry(payload: BuoyTelemetryIn):
    TELEMETRY_STORE.append(payload)
    return payload


@app.post("/api/v1/iot/simulate-event", response_model=BuoyTelemetryIn)
def simulate_flood_and_bloom_event():
    simulated = BuoyTelemetryIn(
        buoy_id="BUOY-SGO-DULCE-01",
        lat=settings.TARGET_LAT,
        lon=settings.TARGET_LON,
        water_level_m=3.15,     # +50% sobre cota base -> Alerta Naranja
        ph=8.9,                 # Alcalinización por fotosíntesis cianobacteriana
        turbidity_ntu=28.5,     # > 20 NTU
        water_temp_c=25.8,      # Rango óptimo cianobacterias (24-26 °C)
        dbo_mg_l=8.4,           # > 5 mg/L
        dqo_mg_l=32.0,          # > 20 mg/L
        phenols_mg_l=0.0018,    # > 0.001 mg/L
    )
    TELEMETRY_STORE.append(simulated)
    return simulated


@app.post("/api/v1/citizen/report", response_model=CitizenReportIn)
def submit_citizen_ground_truth(report: CitizenReportIn):
    CITIZEN_REPORTS_STORE.append(report)
    return report


@app.get("/api/v1/diagnosis/unified", response_model=UnifiedDiagnosisOut)
async def get_unified_diagnosis(lat: float = settings.TARGET_LAT, lon: float = settings.TARGET_LON):
    trends = await nasa_service.analyze_all_satellite_trends(lat, lon)
    precip_72h = await weather_service.get_72h_precipitation_mm(lat, lon)
    latest_buoy = TELEMETRY_STORE[-1] if TELEMETRY_STORE else None

    return compute_unified_diagnosis(
        lat=lat,
        lon=lon,
        satellite_trends=trends,
        buoy=latest_buoy,
        forecast_72h_mm=precip_72h,
        citizen_reports=CITIZEN_REPORTS_STORE,
    )