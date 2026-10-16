"""Endpoints de recomendación de abastecimiento (RF-13 / HU07)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.recommendations.api.schemas import (
    RecommendationListOut,
    RecommendationOut,
    RecommendationRequest,
)
from app.modules.recommendations.application.commands import CreateRecommendationCommand
from app.modules.recommendations.application.facade import RecommendationsFacade
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationOut, status_code=201)
async def create_recommendation(
    body: RecommendationRequest,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    recommendation = await RecommendationsFacade(uow).create(
        CreateRecommendationCommand(
            business_id=user.business_id,
            product_id=body.product_id,
            forecast_days=body.forecast_days,
            created_by=user.user_id,
        )
    )
    return RecommendationOut(**recommendation.__dict__)


@router.get("", response_model=RecommendationListOut)
async def list_recommendations(
    product_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    items = await RecommendationsFacade(uow).list(user.business_id, product_id, limit=limit)
    return RecommendationListOut(items=[RecommendationOut(**item.__dict__) for item in items])
