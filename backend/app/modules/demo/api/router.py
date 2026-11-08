"""Datos de ejemplo para arrancar rápido (solo el dueño)."""
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from app.modules.demo.application.service import DemoFacade
from app.modules.recommendations.application.facade import run_cooccurrence_job
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoStatusOut(BaseModel):
    has_demo: bool
    can_load: bool  # dueño, negocio sin ventas y sin datos de ejemplo
    demo_products: int
    demo_sales: int


class DemoDeletedOut(BaseModel):
    deleted_products: int


@router.get("", response_model=DemoStatusOut)
async def demo_status(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return DemoStatusOut(**(await DemoFacade(uow).status(user.business_id, user.role)).__dict__)


@router.post("", response_model=DemoStatusOut, status_code=201)
async def load_demo(
    background: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    status = await DemoFacade(uow).load(user.business_id, user.role, user.user_id)
    background.add_task(run_cooccurrence_job, user.business_id)  # "productos que suben después" listo
    return DemoStatusOut(**status.__dict__)


@router.delete("", response_model=DemoDeletedOut)
async def delete_demo(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return DemoDeletedOut(deleted_products=await DemoFacade(uow).clear(user.business_id, user.role))
