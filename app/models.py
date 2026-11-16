from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AlertLevel(str, Enum):
    VERDE = "VERDE"         # Sin riesgo
    AMARILLO = "AMARILLO"   # Riesgo bajo / Preventiva
    NARANJA = "NARANJA"     # Riesgo medio / Preparación evacuación + despliegue Biochar
    ROJO = "ROJO"           # Riesgo alto / Evacuación inmediata + prohibición hídrica


class BuoyTelemetryIn(BaseModel):
    buoy_id: str = Field(..., example="BUOY-SGO-01")
    lat: float = Field(default=-27.7850)
    lon: float = Field(default=-64.2450)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    water_level_m: float = Field(..., description="Altura de lámina de agua (m)")
    ph: float = Field(..., description="pH in-situ")
    turbidity_ntu: float = Field(..., description="Turbidez (NTU)")
    water_temp_c: float = Field(..., description="Temperatura del agua (°C)")
    dbo_mg_l: float = Field(..., description="Demanda Biológica de Oxígeno (mg/L)")
    dqo_mg_l: float = Field(..., description="Demanda Química de Oxígeno (mg/L)")
    phenols_mg_l: float = Field(..., description="Concentración de fenoles (mg/L)")


class CitizenReportIn(BaseModel):
    reporter_name: Optional[str] = "Vecino Ribereño"
    lat: float = Field(..., example=-27.7852)
    lon: float = Field(..., example=-64.2448)
    visual_bloom_detected: bool = Field(..., description="Mancha verde / 'yerba' flotante visible")
    shoreline_overflow_detected: bool = Field(..., description="Desborde visible en costa")
    notes: Optional[str] = None
    photo_url: Optional[str] = None


class VariableTrendResult(BaseModel):
    variable: str
    description: str
    unit: str
    trend_direction: str          
    p_value: float
    is_significant: bool         
    sens_slope_per_year: float
    total_change_20yr: float
    latest_value: float
    alert_triggered: bool


class UnifiedDiagnosisOut(BaseModel):
    location: Dict[str, float]
    evaluated_at: datetime
    overall_alert: AlertLevel
    cianosemaforo_status: AlertLevel
    flood_alert_status: AlertLevel
    deploy_biochar_barriers: bool
    recommended_actions: List[str]
    satellite_summary: List[VariableTrendResult]
    latest_buoy: Optional[BuoyTelemetryIn]
    forecast_precip_72h_mm: float
    citizen_validations_count: int