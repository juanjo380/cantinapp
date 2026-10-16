"""Política de recomendación de abastecimiento (RF-13 / HU07). Lógica pura.

Criterio de urgencia (punto abierto #5 del análisis) basado en días de cobertura
de stock frente al tiempo de abastecimiento (lead time).
"""
import math
from dataclasses import dataclass


@dataclass
class RecommendationDraft:
    current_stock: int
    min_stock: int
    lead_time_days: int
    predicted_demand: float
    coverage_days: float | None
    suggested_quantity: int
    urgency: str
    justification: str


def build_recommendation(
    *, current_stock: int, min_stock: int, lead_time_days: int, predicted_demand: float, forecast_days: int
) -> RecommendationDraft:
    daily_demand = predicted_demand / forecast_days if forecast_days > 0 else 0.0
    coverage_days = round(current_stock / daily_demand, 2) if daily_demand > 0 else None

    target = daily_demand * lead_time_days + min_stock
    suggested = max(0, math.ceil(target - current_stock))

    if current_stock <= 0:
        urgency = "ALTO"
    elif daily_demand <= 0:
        urgency = "BAJO"
    elif coverage_days is not None and coverage_days < lead_time_days:
        urgency = "ALTO"
    elif current_stock < min_stock or (coverage_days is not None and coverage_days < lead_time_days * 2):
        urgency = "MEDIO"
    else:
        urgency = "BAJO"

    coverage_text = f"{coverage_days} días" if coverage_days is not None else "sin demanda estimada"
    if current_stock <= 0:
        justification = (
            f"Producto agotado. Demanda diaria estimada {daily_demand:.2f} u/día; "
            f"se sugiere reponer {suggested} unidades para cubrir {lead_time_days} días de abastecimiento."
        )
    else:
        justification = (
            f"Cobertura actual {coverage_text} frente a {lead_time_days} días de abastecimiento. "
            f"Demanda diaria estimada {daily_demand:.2f} u/día, stock mínimo {min_stock}."
        )

    return RecommendationDraft(
        current_stock=current_stock,
        min_stock=min_stock,
        lead_time_days=lead_time_days,
        predicted_demand=round(predicted_demand, 2),
        coverage_days=coverage_days,
        suggested_quantity=suggested,
        urgency=urgency,
        justification=justification,
    )
