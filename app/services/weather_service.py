from datetime import datetime, timedelta
import httpx
from app.config import settings


class MeteomaticsService:
    async def get_72h_precipitation_mm(self, lat: float, lon: float) -> float:
        """Consulta precipitación acumulada proyectada a 72h vía Meteomatics API."""
        if not settings.METEOMATICS_USER or not settings.METEOMATICS_PASS:
            # Valor de respaldo operativo si no hay credenciales activas en entorno local
            return 34.5

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (datetime.utcnow() + timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = f"https://api.meteomatics.com/{now}--{end}:PT1H/precip_1h:mm/{lat},{lon}/json"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, auth=(settings.METEOMATICS_USER, settings.METEOMATICS_PASS))
            resp.raise_for_status()
            data = resp.json()

        dates = data["data"][0]["coordinates"][0]["dates"]
        total_mm = sum(entry["value"] for entry in dates)
        return round(float(total_mm), 2)