"""Endpoints de análisis histórico (RF-10, RF-11 / HU05)."""
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.analytics.api.schemas import (
    ProductRankingListOut,
    ProductRankingOut,
    SalesSeriesOut,
    SeriesPointOut,
)
from app.modules.analytics.application.facade import AnalyticsFacade
from app.modules.analytics.application.queries import ProductRankingQuery, SalesSeriesQuery
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/sales", response_model=SalesSeriesOut)
async def sales_series(
    period: str = Query("daily", description="daily | weekly | monthly | yearly"),
    date_from: date | None = None,
    date_to: date | None = None,
    product_id: UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=29))
    series = await AnalyticsFacade(uow).sales_series(
        SalesSeriesQuery(
            business_id=user.business_id,
            period=period,
            date_from=date_from,
            date_to=date_to,
            product_id=product_id,
        )
    )
    return SalesSeriesOut(
        period=period,
        date_from=date_from,
        date_to=date_to,
        series=[SeriesPointOut(**point.__dict__) for point in series],
    )


@router.get("/top-products", response_model=ProductRankingListOut)
async def top_products(
    order: str = Query("top", pattern="^(top|bottom)$"),
    limit: int = Query(10, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    date_to = date_to or date.today()
    date_from = date_from or (date_to - timedelta(days=29))
    items = await AnalyticsFacade(uow).product_ranking(
        ProductRankingQuery(
            business_id=user.business_id,
            order=order,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )
    )
    return ProductRankingListOut(order=order, items=[ProductRankingOut(**item.__dict__) for item in items])
