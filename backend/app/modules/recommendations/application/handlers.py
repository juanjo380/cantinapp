"""Handler de recomendación. Combina inventario + predicción (regla de
dependencia: Recomendación llama a Predicción e Inventario)."""
from app.core.exceptions import NotFoundError
from app.modules.forecasting.domain.entities import Forecast
from app.modules.inventory.domain.repository import InventoryRepository
from app.modules.products.domain.repository import ProductRepository
from app.modules.recommendations.domain.policy import build_recommendation
from app.modules.recommendations.domain.repository import RecommendationRepository


async def create_recommendation(
    recommendations: RecommendationRepository,
    inventory: InventoryRepository,
    products: ProductRepository,
    business_id,
    product_id,
    forecast: Forecast,
):
    if await products.get(business_id, product_id) is None:
        raise NotFoundError("Producto no encontrado")
    item = await inventory.get(business_id, product_id)
    if item is None:
        raise NotFoundError("Producto no encontrado en inventario")

    draft = build_recommendation(
        current_stock=item.stock_quantity,
        min_stock=item.min_stock,
        lead_time_days=item.lead_time_days,
        predicted_demand=float(forecast.predicted_demand),
        forecast_days=forecast.forecast_days,
    )
    return await recommendations.add(
        business_id=business_id, product_id=product_id, forecast_id=forecast.id, draft=draft
    )
