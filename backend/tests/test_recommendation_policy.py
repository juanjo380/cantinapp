from app.modules.recommendations.domain.policy import build_recommendation


def test_agotado_is_high_urgency():
    draft = build_recommendation(
        current_stock=0, min_stock=5, lead_time_days=7, predicted_demand=70, forecast_days=30
    )
    assert draft.urgency == "ALTO"
    assert draft.suggested_quantity > 0


def test_healthy_stock_is_low_urgency():
    draft = build_recommendation(
        current_stock=100, min_stock=5, lead_time_days=7, predicted_demand=70, forecast_days=30
    )
    assert draft.urgency == "BAJO"
    assert draft.suggested_quantity == 0


def test_low_coverage_is_medium_or_high():
    draft = build_recommendation(
        current_stock=10, min_stock=5, lead_time_days=7, predicted_demand=70, forecast_days=30
    )
    assert draft.urgency in ("MEDIO", "ALTO")
    assert draft.coverage_days is not None
