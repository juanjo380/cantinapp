"""Endpoints del negocio activo: perfil, sedes y equipo. Los permisos se validan en los handlers."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.auth.api.router import auth_out
from app.modules.auth.api.schemas import AuthResponse
from app.modules.auth.application.commands import SwitchBusinessCommand
from app.modules.auth.application.facade import AuthFacade
from app.modules.business.api.schemas import (
    BusinessOut,
    BusinessUpdate,
    DataSharing,
    InvitationAccept,
    InvitationCreate,
    InvitationCreated,
    InvitationOut,
    InvitationPreview,
    LocationIn,
    LocationOut,
    MemberOut,
    RoleChange,
)
from app.modules.business.application.commands import (
    AcceptInvitationCommand,
    ChangeRoleCommand,
    InviteMemberCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.business.application.facade import BusinessFacade
from app.shared.api.dependencies import CurrentAccount, CurrentUser, get_current_account, get_current_user
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


@router.get("/data-sharing", response_model=DataSharing)
async def get_data_sharing(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return DataSharing(enabled=await BusinessFacade(uow).ml_data_sharing(user.business_id))


@router.put("/data-sharing", response_model=DataSharing)
async def set_data_sharing(
    body: DataSharing,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    return DataSharing(enabled=await BusinessFacade(uow).set_ml_data_sharing(user, body.enabled))


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


# Al equipo solo se entra por invitación: enlace al correo + código que dicta quien invita.
@router.get("/invitations", response_model=list[InvitationOut])
async def list_invitations(
    user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    return [i.__dict__ for i in await BusinessFacade(uow).invitations(user)]


@router.post("/invitations", response_model=InvitationCreated, status_code=201)
async def invite_member(
    body: InvitationCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    invitation, code = await BusinessFacade(uow).invite(
        InviteMemberCommand(actor=user, email=body.email, role=body.role, location_id=body.location_id)
    )
    return {**invitation.__dict__, "code": code}


@router.delete("/invitations/{invitation_id}", status_code=204)
async def revoke_invitation(
    invitation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    await BusinessFacade(uow).revoke_invitation(user, invitation_id)
    return None


# Las usa la persona invitada: tiene sesión pero aún no pertenece al negocio (CurrentAccount).
@router.get("/invitations/preview", response_model=InvitationPreview)
async def preview_invitation(
    token: str = Query(min_length=10, max_length=200),
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    return (await BusinessFacade(uow).invitation(account.email, token)).__dict__


@router.post("/invitations/accept", response_model=AuthResponse)
async def accept_invitation(
    body: InvitationAccept,
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    """Entra al negocio y devuelve la sesión ya abierta en él."""
    business_id = await BusinessFacade(uow).accept_invitation(
        AcceptInvitationCommand(user_id=account.user_id, email=account.email, token=body.token, code=body.code)
    )
    result = await AuthFacade(uow).switch(SwitchBusinessCommand(user_id=account.user_id, business_id=business_id))
    return auth_out(result)


@router.patch("/members/{user_id}", response_model=MemberOut)
async def change_role(
    user_id: UUID,
    body: RoleChange,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    member = await BusinessFacade(uow).change_role(
        ChangeRoleCommand(actor=user, user_id=user_id, role=body.role, location_id=body.location_id)
    )
    return member.__dict__


@router.delete("/members/{user_id}", status_code=204)
async def remove_member(
    user_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    await BusinessFacade(uow).remove_member(RemoveMemberCommand(actor=user, user_id=user_id))
    return None
