import numpy as np
import pandas as pd
import pymannkendall as mk
from app.config import settings
from app.models import VariableTrendResult


def evaluate_20yr_trend(
    series: pd.Series,
    var_code: str,
    description: str,
    unit: str,
    threshold: float,
    high_is_risk: bool = True,
) -> VariableTrendResult:
    """
    Agrega datos diarios a promedios/máximos anuales (2006-2026),
    ejecuta Mann-Kendall + Sen's Slope y filtra por p < 0.05.
    """
    clean_series = series.replace(-999.0, np.nan).dropna()
    annual = clean_series.resample("YE").mean().dropna()

    if len(annual) < 5:
        raise ValueError(f"Serie insuficiente para Mann-Kendall en {var_code}")

    result = mk.original_test(annual.values, alpha=settings.SIGNIFICANCE_ALPHA)
    p_val = float(result.p)
    is_sig = bool(p_val < settings.SIGNIFICANCE_ALPHA)
    slope_yr = float(result.slope)
    total_change = round(slope_yr * len(annual), 4)
    latest_val = float(clean_series.iloc[-1])

    if high_is_risk:
        alert = (latest_val >= threshold) or (is_sig and slope_yr > 0 and annual.iloc[-1] >= threshold * 0.9)
    else:
        alert = (latest_val <= threshold) or (is_sig and slope_yr < 0 and annual.iloc[-1] <= threshold * 1.1)

    return VariableTrendResult(
        variable=var_code,
        description=description,
        unit=unit,
        trend_direction=result.trend,
        p_value=round(p_val, 6),
        is_significant=is_sig,
        sens_slope_per_year=round(slope_yr, 5),
        total_change_20yr=total_change,
        latest_value=round(latest_val, 3),
        alert_triggered=bool(alert),
    )