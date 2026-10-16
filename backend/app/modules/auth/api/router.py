"""Endpoints de autenticación (RF-01, RF-02)."""
from fastapi import APIRouter, Depends

from app.modules.auth.api.schemas import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.modules.auth.application.commands import LoginCommand, RegisterCommand
from app.modules.auth.application.facade import AuthFacade
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user) -> UserOut:
    return UserOut(id=user.id, business_id=user.business_id, email=user.email, full_name=user.full_name)


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    result = await AuthFacade(uow).register(
        RegisterCommand(
            business_name=body.business_name,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    )
    return AuthResponse(
        token=result.token,
        user=_user_out(result.user),
        business_id=result.business.id,
        business_name=result.business.name,
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    result = await AuthFacade(uow).login(LoginCommand(email=body.email, password=body.password))
    return AuthResponse(token=result.token, user=_user_out(result.user), business_id=result.user.business_id)


@router.post("/logout", status_code=204)
async def logout(_: CurrentUser = Depends(get_current_user)):
    # JWT sin estado: el cliente descarta el token.
    return None


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser = Depends(get_current_user)):
    return UserOut(
        id=user.user_id, business_id=user.business_id, email=user.email, full_name=user.full_name
    )
