"""Endpoints de autenticación, perfil del usuario y negocio activo (RF-01, RF-02)."""
from fastapi import APIRouter, Depends

from app.modules.auth.api.schemas import (
    AuthResponse,
    CreateBusinessRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PasswordChange,
    ProfileUpdate,
    RegisterRequest,
    ResetPasswordRequest,
    SessionOut,
    SwitchBusinessRequest,
)
from app.modules.auth.application.commands import (
    ChangePasswordCommand,
    CreateBusinessCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    SwitchBusinessCommand,
    UpdateProfileCommand,
)
from app.modules.auth.application.facade import AuthFacade, AuthResult
from app.modules.auth.domain.entities import Session
from app.shared.api.dependencies import CurrentAccount, get_current_account
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _session_out(session: Session) -> dict:
    user = session.user
    return {
        "user": {
            "id": user.id,
            "business_id": session.business_id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "job_title": user.job_title,
        },
        "business_id": session.business_id,
        "business_name": session.business_name,
        "role": session.role,
        "profile_completed": session.profile_completed,
        "businesses": [m.__dict__ for m in session.businesses],
    }


def auth_out(result: AuthResult) -> AuthResponse:
    return AuthResponse(token=result.token, **_session_out(result.session))


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    result = await AuthFacade(uow).register(
        RegisterCommand(
            business_name=body.business_name,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            consents={
                "TERMS": body.accept_terms,
                "PRIVACY": body.accept_privacy,
                "ML_ANONYMOUS": body.allow_ml_data,
            },
        )
    )
    return auth_out(result)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return auth_out(await AuthFacade(uow).login(LoginCommand(email=body.email, password=body.password)))


@router.post("/logout", status_code=204)
async def logout(_: CurrentAccount = Depends(get_current_account)):
    # JWT sin estado: el cliente descarta el token.
    return None


@router.get("/me", response_model=SessionOut)
async def me(account: CurrentAccount = Depends(get_current_account), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return _session_out(await AuthFacade(uow).session(account.user_id, account.business_id))


@router.put("/me", response_model=SessionOut)
async def update_me(
    body: ProfileUpdate,
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    session = await AuthFacade(uow).update_profile(
        UpdateProfileCommand(user_id=account.user_id, changes=body.model_dump(exclude_unset=True)),
        account.business_id,
    )
    return _session_out(session)


@router.put("/password", response_model=AuthResponse)
async def change_password(
    body: PasswordChange,
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    """Devuelve un token nuevo: el anterior y las demás sesiones quedan cerradas."""
    result = await AuthFacade(uow).change_password(
        ChangePasswordCommand(
            user_id=account.user_id,
            email=account.email,
            current_password=body.current_password,
            new_password=body.new_password,
        ),
        account.business_id,
    )
    return auth_out(result)


@router.post("/password/forgot", status_code=202)
async def forgot_password(body: ForgotPasswordRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    """Misma respuesta exista o no la cuenta."""
    await AuthFacade(uow).request_password_reset(RequestPasswordResetCommand(email=body.email))
    return {"detail": "Si el correo está registrado, te enviamos un código. Vence en 5 minutos."}


@router.post("/password/reset", status_code=204)
async def reset_password(body: ResetPasswordRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    await AuthFacade(uow).reset_password(
        ResetPasswordCommand(email=body.email, code=body.code, new_password=body.new_password)
    )
    return None


@router.post("/switch", response_model=AuthResponse)
async def switch_business(
    body: SwitchBusinessRequest,
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    result = await AuthFacade(uow).switch(
        SwitchBusinessCommand(user_id=account.user_id, business_id=body.business_id)
    )
    return auth_out(result)


@router.post("/businesses", response_model=AuthResponse, status_code=201)
async def create_business(
    body: CreateBusinessRequest,
    account: CurrentAccount = Depends(get_current_account),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    result = await AuthFacade(uow).create_business(CreateBusinessCommand(user_id=account.user_id, name=body.name))
    return auth_out(result)
