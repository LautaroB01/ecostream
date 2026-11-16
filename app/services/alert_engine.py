from datetime import datetime
from typing import List, Optional
from app.config import settings
from app.models import (
    AlertLevel,
    BuoyTelemetryIn,
    CitizenReportIn,
    UnifiedDiagnosisOut,
    VariableTrendResult,
)


def compute_unified_diagnosis(
    lat: float,
    lon: float,
    satellite_trends: List[VariableTrendResult],
    buoy: Optional[BuoyTelemetryIn],
    forecast_72h_mm: float,
    citizen_reports: List[CitizenReportIn],
) -> UnifiedDiagnosisOut:
    actions: List[str] = []

    # 1. Evaluación Satelital y Pronóstico (Capa Macro)
    sig_satellite_alerts = [t for t in satellite_trends if t.is_significant and t.alert_triggered]
    has_sig_trend = len(sig_satellite_alerts) > 0

    # 2. Evaluación de Riesgo de Inundación (Capa Meso + Meteomatics)
    flood_level = AlertLevel.VERDE
    if forecast_72h_mm >= settings.PRECIP_EXTREME_MM or has_sig_trend:
        flood_level = AlertLevel.AMARILLO
        actions.append("Alerta Amarilla Hídrica: Inspeccionar drenajes y alistar mangas de Biochar.")

    if buoy:
        rise_ratio = (buoy.water_level_m - settings.WATER_LEVEL_BASE_M) / settings.WATER_LEVEL_BASE_M
        if buoy.water_level_m >= settings.FLOOD_CRITICAL_RED_M:
            flood_level = AlertLevel.ROJO
            actions.append("EVACUACIÓN INMEDIATA (ROJO): Nivel crítico de desborde alcanzado. Dirigirse a zonas altas.")
        elif rise_ratio >= settings.FLOOD_RISE_ORANGE_PCT:
            flood_level = AlertLevel.NARANJA
            actions.append("Alerta Naranja Inundación (+40% cota base): Preparar documentos, medicamentos y kit de emergencia.")

    # 3. Evaluación del Cianosemáforo (Eutrofización y Toxinas)
    ciano_level = AlertLevel.VERDE
    if has_sig_trend:
        ciano_level = AlertLevel.AMARILLO

    if buoy:
        bio_score = 0
        if buoy.ph > settings.PH_ALKALINE_ALERT:
            bio_score += 1
        if buoy.turbidity_ntu > settings.TURBIDITY_ALERT_NTU:
            bio_score += 1
        if buoy.water_temp_c >= settings.WATER_TEMP_ALERT_C:
            bio_score += 1
        if buoy.dbo_mg_l > settings.DBO_ALERT_MG_L:
            bio_score += 1
        if buoy.dqo_mg_l > settings.DQO_ALERT_MG_L or buoy.phenols_mg_l > settings.PHENOLS_ALERT_MG_L:
            bio_score += 2

        if bio_score >= 4:
            ciano_level = AlertLevel.ROJO
            actions.append("Cianosemáforo ROJO: Prohibido ingresar al agua, pescar o consumir agua del río (riesgo de microcistinas).")
        elif bio_score >= 2:
            ciano_level = AlertLevel.NARANJA
            actions.append("Cianosemáforo NARANJA: Evitar contacto con manchas verdes en orilla; desplegar barreras de Biochar.")
        elif bio_score == 1 and ciano_level == AlertLevel.VERDE:
            ciano_level = AlertLevel.AMARILLO

    # 4. Validación Ciudadana (Capa Micro)
    recent_bloom_photos = sum(1 for r in citizen_reports if r.visual_bloom_detected)
    recent_overflow_photos = sum(1 for r in citizen_reports if r.shoreline_overflow_detected)

    if recent_bloom_photos > 0 and ciano_level == AlertLevel.VERDE:
        ciano_level = AlertLevel.AMARILLO
        actions.append("Validación ciudadana: Floración incipiente reportada en costa.")
    if recent_overflow_photos > 0 and flood_level in (AlertLevel.VERDE, AlertLevel.AMARILLO):
        flood_level = AlertLevel.NARANJA
        actions.append("Validación ciudadana: Aniegos costeros confirmados por fotografía georreferenciada.")

    # 5. Nivel Global y Orden de Mitigación Circular con Biochar
    severity_order = {
        AlertLevel.VERDE: 0,
        AlertLevel.AMARILLO: 1,
        AlertLevel.NARANJA: 2,
        AlertLevel.ROJO: 3,
    }
    overall = max([flood_level, ciano_level], key=lambda lvl: severity_order[lvl])
    deploy_biochar = severity_order[overall] >= severity_order[AlertLevel.NARANJA] or has_sig_trend

    if deploy_biochar:
        actions.append("MITIGACIÓN ACTIVA: Desplegar mangas flotantes de geotextil HDPE con Biochar pirolizado (450-550 °C) y programar retiro/compostaje a 15 días.")

    if not actions:
        actions.append("Condiciones normales (VERDE): Agua apta para uso recreativo y pesca. Monitoreo continuo activo.")

    return UnifiedDiagnosisOut(
        location={"lat": lat, "lon": lon},
        evaluated_at=datetime.utcnow(),
        overall_alert=overall,
        cianosemaforo_status=ciano_level,
        flood_alert_status=flood_level,
        deploy_biochar_barriers=deploy_biochar,
        recommended_actions=actions,
        satellite_summary=satellite_trends,
        latest_buoy=buoy,
        forecast_precip_72h_mm=forecast_72h_mm,
        citizen_validations_count=len(citizen_reports),
    )