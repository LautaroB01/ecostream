from datetime import datetime, timedelta
import httpx
import pandas as pd
import planetary_computer
import pystac_client
from app.config import settings
from app.models import VariableTrendResult
from app.services.stats_engine import evaluate_20yr_trend


class NasaSatelliteService:
    async def fetch_nasa_power_20yr(self, lat: float, lon: float) -> pd.DataFrame:
        """Descarga 20 años (2006-2026) de variables hidrometeorológicas de NASA POWER."""
        params = {
            "parameters": "T2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR,RH2M",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": settings.START_DATE,
            "end": settings.END_DATE,
            "format": "JSON",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(settings.NASA_POWER_URL, params=params)
            resp.raise_for_status()
            payload = resp.json()

        param_data = payload["properties"]["parameter"]
        df = pd.DataFrame(param_data)
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
        return df

    def query_planetary_computer_scenes(self, lat: float, lon: float, days_back: int = 30) -> dict:
        """
        Consulta escenas recientes en Microsoft Planetary Computer (MODIS / Sentinel-2)
        para cálculo de máscara de agua (NDWI > 0.10) y floraciones (MODIS/PACE).
        """
        catalog = pystac_client.Client.open(
            settings.PLANETARY_COMPUTER_STAC,
            modifier=planetary_computer.sign_inplace,
        )
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=days_back)
        bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]

        search = catalog.search(
            collections=["sentinel-2-l2a", "modis-13Q1-061"],
            bbox=bbox,
            datetime=f"{start_dt.strftime('%Y-%m-%d')}/{end_dt.strftime('%Y-%m-%d')}",
            limit=5,
        )
        items = list(search.items())
        return {
            "stac_endpoint": settings.PLANETARY_COMPUTER_STAC,
            "scenes_found": len(items),
            "latest_scene_id": items[0].id if items else None,
            "latest_datetime": items[0].datetime.isoformat() if items else None,
            "ndwi_threshold": settings.NDWI_WATER_MASK,
        }

    async def analyze_all_satellite_trends(self, lat: float, lon: float) -> list[VariableTrendResult]:
        df = await self.fetch_nasa_power_20yr(lat, lon)
        trends = [
            evaluate_20yr_trend(
                df["T2M"], "T2M", "Temperatura del aire a 2m", "°C",
                settings.TEMP_HEATWAVE_C, high_is_risk=True
            ),
            evaluate_20yr_trend(
                df["ALLSKY_SFC_SW_DWN"], "ALLSKY_SFC_SW_DWN", "Irradiancia solar superficial", "kWh/m²/día",
                settings.SOLAR_RAD_MIN_KWH, high_is_risk=True
            ),
            evaluate_20yr_trend(
                df["PRECTOTCORR"], "PRECTOTCORR", "Precipitación diaria corregida", "mm/día",
                settings.PRECIP_EXTREME_MM, high_is_risk=True
            ),
            evaluate_20yr_trend(
                df["RH2M"], "RH2M", "Humedad relativa a 2m", "%",
                settings.HUMIDITY_DEFICIT_PCT, high_is_risk=False
            ),
        ]
        return trends