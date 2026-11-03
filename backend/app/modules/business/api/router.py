"""Endpoints del negocio activo: perfil, sedes y equipo. Los permisos se validan en los handlers."""
from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.business.api.schemas import (
    BusinessOut,
    BusinessUpdate,
    LocationIn,
    LocationOut,
    MemberAdd,
    MemberOut,
    RoleChange,
)
from app.modules.business.application.commands import (
    AddMemberCommand,
    ChangeRoleCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.business.application.facade import BusinessFacade
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/business", tags=["business"])


@router.get("", response_model=BusinessOut)
async def get_business(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return (await BusinessFacade(uow).get(user.business_id)).__dict__


@router.put("", response_model=BusinessOut)
async def update_business(
    body: BusinessUpdate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    profile = await BusinessFacade(uow).update(
        UpdateBusinessCommand(actor=user, changes=body.model_dump(exclude_unset=True))
    )
    return profile.__dict__


@router.get("/locations", response_model=list[LocationOut])
async def list_locations(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return [loc.__dict__ for loc in await BusinessFacade(uow).locations(user.business_id)]


@router.post("/locations", response_model=LocationOut, status_code=201)
async def create_location(
    body: LocationIn,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    location = await BusinessFacade(uow).save_location(
        SaveLocationCommand(actor=user, location_id=None, data=body.model_dump())
    )
    return location.__dict__


@router.put("/locations/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: UUID,
    body: LocationIn,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    location = await BusinessFacade(uow).save_location(
        SaveLocationCommand(actor=user, location_id=location_id, data=body.model_dump())
    )
    return location.__dict__


@router.delete("/locations/{location_id}", status_code=204)
async def delete_location(
    location_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    await BusinessFacade(uow).delete_location(user, location_id)
    return None


@router.get("/members", response_model=list[MemberOut])
async def list_members(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return [m.__dict__ for m in await BusinessFacade(uow).members(user.business_id)]


@router.post("/members", response_model=MemberOut, status_code=201)
async def add_member(
    body: MemberAdd,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    member = await BusinessFacade(uow).add_member(AddMemberCommand(actor=user, email=body.email, role=body.role))
    return member.__dict__


@router.patch("/members/{user_id}", response_model=MemberOut)
async def change_role(
    user_id: UUID,
    body: RoleChange,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    member = await BusinessFacade(uow).change_role(ChangeRoleCommand(actor=user, user_id=user_id, role=body.role))
    return member.__dict__


@router.delete("/members/{user_id}", status_code=204)
async def remove_member(
    user_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    await BusinessFacade(uow).remove_member(RemoveMemberCommand(actor=user, user_id=user_id))
    return None
