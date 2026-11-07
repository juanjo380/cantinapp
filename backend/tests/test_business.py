import asyncio
from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from app.core.security import MAX_CODE_ATTEMPTS
from app.modules.auth.application import handlers as auth_handlers
from app.modules.auth.application.commands import SwitchBusinessCommand
from app.modules.auth.domain.entities import Membership, User, build_session
from app.modules.business.api.schemas import BusinessUpdate
from app.modules.business.application import handlers
from app.modules.business.application.commands import (
    AcceptInvitationCommand,
    ChangeRoleCommand,
    InviteMemberCommand,
    RemoveMemberCommand,
)
from app.modules.business.domain.entities import Invitation, Member, nit_check_digit, normalize_nit
from app.shared.api.dependencies import CurrentUser

BID = uuid4()


def run(coro):
    return asyncio.run(coro)


# --- NIT ----------------------------------------------------------------------

def test_nit_check_digit_matches_dian():
    assert nit_check_digit("800197268") == 4  # NIT de la DIAN: 800.197.268-4
    assert normalize_nit("800.197.268-4") == "800197268-4"
    assert normalize_nit("800197268") == "800197268"
    for bad in ("800197268-5", "abc", "12-34", "123"):
        with pytest.raises(ValueError):
            normalize_nit(bad)


def test_business_update_rejects_bad_nit_and_blank_name():
    assert BusinessUpdate(tax_id=" ", city="").model_dump(exclude_unset=True) == {"tax_id": None, "city": None}
    with pytest.raises(ValueError):
        BusinessUpdate(tax_id="800197268-5")
    with pytest.raises(ValueError):
        BusinessUpdate(name="  ")


# --- sesión / negocio activo ---------------------------------------------------

def _user(full_name="Ana"):
    return User(id=uuid4(), business_id=None, email="a@b.co", full_name=full_name, is_active=True)


def test_build_session_picks_preferred_member_business_or_none():
    a, b = Membership(uuid4(), "A", "OWNER", True), Membership(uuid4(), "B", "MEMBER", False)
    session = build_session(_user(), [a, b], [uuid4(), b.business_id])
    assert (session.business_name, session.role, session.profile_completed) == ("B", "MEMBER", False)
    assert build_session(_user(), [a], [uuid4()]).business_id is None
    # el perfil también exige el nombre del usuario
    assert build_session(_user(full_name=None), [a], [a.business_id]).profile_completed is False
    assert build_session(_user(), [a], [a.business_id]).profile_completed is True


def test_switch_to_foreign_business_is_not_found():
    user = _user()

    class Users:
        async def get_by_id(self, _):
            return user

    class Memberships:
        async def list_for_user(self, _):
            return [Membership(uuid4(), "Mío", "OWNER", True)]

    with pytest.raises(NotFoundError):
        run(auth_handlers.switch_business(Users(), Memberships(), SwitchBusinessCommand(user.id, uuid4())))


# --- equipo ---------------------------------------------------------------------

class FakeRepo:
    def __init__(self):
        self.owner, self.member = uuid4(), uuid4()
        self.outsider = uuid4()
        self.roles = {self.owner: "OWNER", self.member: "MEMBER"}

    async def get_member(self, business_id, user_id):
        role = self.roles.get(user_id)
        return role and Member(user_id, "x@y.co", None, None, role, datetime.now())

    async def find_user_id(self, email):
        return self.outsider if email == "nuevo@y.co" else None

    async def add_member(self, business_id, user_id, role):
        self.roles[user_id] = role

    async def set_role(self, business_id, user_id, role):
        self.roles[user_id] = role

    async def remove_member(self, business_id, user_id):
        del self.roles[user_id]

    # invitaciones: un solo slot basta para el test
    async def add_invitation(self, *, business_id, email, role, invited_by, token_hash, code_hash, expires_at):
        self.invitation = Invitation(uuid4(), business_id, "Tienda", email, role, "Dueña", expires_at, datetime.now(), code_hash)
        self.token_hash = token_hash
        return self.invitation

    async def find_invitation(self, token_hash):
        return self.invitation if getattr(self, "token_hash", None) == token_hash else None

    async def count_invitation_attempt(self, invitation_id):
        self.invitation.attempts += 1

    async def accept_invitation(self, invitation_id):
        self.token_hash = None


def actor(repo, user_id):
    return CurrentUser(user_id=user_id, business_id=BID, email="x@y.co", full_name=None, role=repo.roles[user_id])


def test_only_admins_manage_team_and_owner_is_untouchable():
    repo = FakeRepo()
    owner, member = actor(repo, repo.owner), actor(repo, repo.member)

    with pytest.raises(ForbiddenError):
        run(handlers.invite_member(repo, InviteMemberCommand(member, "nuevo@y.co", "MEMBER")))
    with pytest.raises(NotFoundError):
        run(handlers.invite_member(repo, InviteMemberCommand(owner, "nadie@y.co", "MEMBER")))
    accept_invitation(repo, "ADMIN")
    assert repo.roles[repo.outsider] == "ADMIN"
    with pytest.raises(ConflictError):
        run(handlers.invite_member(repo, InviteMemberCommand(owner, "nuevo@y.co", "MEMBER")))

    admin = actor(repo, repo.outsider)
    with pytest.raises(ForbiddenError):
        run(handlers.change_role(repo, ChangeRoleCommand(admin, repo.owner, "MEMBER")))
    with pytest.raises(ForbiddenError):
        run(handlers.remove_member(repo, RemoveMemberCommand(admin, repo.owner)))
    with pytest.raises(ForbiddenError):  # un miembro no saca a otros
        run(handlers.remove_member(repo, RemoveMemberCommand(member, repo.outsider)))

    run(handlers.remove_member(repo, RemoveMemberCommand(member, repo.member)))  # pero sí puede salirse
    assert repo.member not in repo.roles


def accept_invitation(repo, role):
    """Invita a nuevo@y.co y acepta con su cuenta y el código correcto."""
    owner = actor(repo, repo.owner)
    _, token, code = run(handlers.invite_member(repo, InviteMemberCommand(owner, "nuevo@y.co", role)))
    return run(handlers.accept_invitation(repo, AcceptInvitationCommand(repo.outsider, "nuevo@y.co", token, code)))


def test_invitation_needs_the_invited_account_and_the_security_code():
    repo = FakeRepo()
    owner = actor(repo, repo.owner)
    _, token, code = run(handlers.invite_member(repo, InviteMemberCommand(owner, "nuevo@y.co", "MEMBER")))
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"

    def accept(email, given_code, given_token=token):
        return run(
            handlers.accept_invitation(repo, AcceptInvitationCommand(repo.outsider, email, given_token, given_code))
        )

    with pytest.raises(ForbiddenError):  # el enlace llegó a otra persona
        accept("otro@y.co", code)
    with pytest.raises(NotFoundError):  # enlace inventado
        accept("nuevo@y.co", code, "token-que-no-existe")
    with pytest.raises(UnprocessableError):
        accept("nuevo@y.co", wrong)
    assert repo.outsider not in repo.roles

    assert accept("NUEVO@y.co", code) == BID
    assert repo.roles[repo.outsider] == "MEMBER"
    with pytest.raises(NotFoundError):  # un solo uso
        accept("nuevo@y.co", code)


def test_invitation_is_void_after_too_many_wrong_codes():
    repo = FakeRepo()
    owner = actor(repo, repo.owner)
    _, token, code = run(handlers.invite_member(repo, InviteMemberCommand(owner, "nuevo@y.co", "MEMBER")))
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"
    for _ in range(MAX_CODE_ATTEMPTS):
        with pytest.raises(UnprocessableError):
            run(handlers.accept_invitation(repo, AcceptInvitationCommand(repo.outsider, "nuevo@y.co", token, wrong)))
    with pytest.raises(NotFoundError):
        run(handlers.accept_invitation(repo, AcceptInvitationCommand(repo.outsider, "nuevo@y.co", token, code)))
    assert repo.outsider not in repo.roles
