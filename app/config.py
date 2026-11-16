from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcoStream Sgo API"
    VERSION: str = "1.0.0"

    # Coordenadas Río Dulce Capital, Santiago del Estero
    TARGET_LAT: float = -27.7850
    TARGET_LON: float = -64.2450
    START_DATE: str = "20060101"
    END_DATE: str = "20261101"

    # Endpoints oficiales
    NASA_POWER_URL: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    PLANETARY_COMPUTER_STAC: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    METEOMATICS_USER: str = ""
    METEOMATICS_PASS: str = ""

    # Umbrales Satelitales y Climáticos
    SIGNIFICANCE_ALPHA: float = 0.05       # 95% de confianza estadística
    TEMP_HEATWAVE_C: float = 35.0          # T2M > 35 °C
    SOLAR_RAD_MIN_KWH: float = 6.5         # ALLSKY_SFC_SW_DWN > 6.5-7.5 kWh/m²/día
    PRECIP_EXTREME_MM: float = 30.0        # PRECTOTCORR 30-50 mm en 24h
    HUMIDITY_DEFICIT_PCT: float = 35.0     # RH2M < 30-35%
    NDWI_WATER_MASK: float = 0.10          # NDWI > 0.10 máscara de agua
    CHLOROPHYLL_ALERT_MG_M3: float = 10.0  # Chlorophyll-a 10-15 mg/m³

    # Umbrales Biosensor IoT In-Situ
    WATER_LEVEL_BASE_M: float = 2.10       # Cota base Río Dulce (m)
    FLOOD_RISE_ORANGE_PCT: float = 0.40    # +40% sobre nivel base -> Alerta Naranja
    FLOOD_CRITICAL_RED_M: float = 3.50     # Cota de desborde -> Evacuación Roja
    PH_ALKALINE_ALERT: float = 8.5         # pH > 8.5 (consumo CO2 ciclo de Calvin)
    TURBIDITY_ALERT_NTU: float = 20.0      # Turbidez > 20-30 NTU
    WATER_TEMP_ALERT_C: float = 24.0       # Temp agua 24-26 °C
    DBO_ALERT_MG_L: float = 5.0            # DBO > 5-10 mg/L
    DQO_ALERT_MG_L: float = 20.0           # DQO > 20-40 mg/L
    PHENOLS_ALERT_MG_L: float = 0.001      # Fenoles > 0.001-0.002 mg/L

    class Config:
        env_file = ".env"


settings = Settings()