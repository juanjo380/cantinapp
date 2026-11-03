import asyncio
from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.auth.application import handlers as auth_handlers
from app.modules.auth.application.commands import SwitchBusinessCommand
from app.modules.auth.domain.entities import Membership, User, build_session
from app.modules.business.api.schemas import BusinessUpdate
from app.modules.business.application import handlers
from app.modules.business.application.commands import AddMemberCommand, ChangeRoleCommand, RemoveMemberCommand
from app.modules.business.domain.entities import Member, nit_check_digit, normalize_nit
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


def actor(repo, user_id):
    return CurrentUser(user_id=user_id, business_id=BID, email="x@y.co", full_name=None, role=repo.roles[user_id])


def test_only_admins_manage_team_and_owner_is_untouchable():
    repo = FakeRepo()
    owner, member = actor(repo, repo.owner), actor(repo, repo.member)

    with pytest.raises(ForbiddenError):
        run(handlers.add_member(repo, AddMemberCommand(member, "nuevo@y.co", "MEMBER")))
    with pytest.raises(NotFoundError):
        run(handlers.add_member(repo, AddMemberCommand(owner, "nadie@y.co", "MEMBER")))
    assert run(handlers.add_member(repo, AddMemberCommand(owner, "nuevo@y.co", "ADMIN"))).role == "ADMIN"
    with pytest.raises(ConflictError):
        run(handlers.add_member(repo, AddMemberCommand(owner, "nuevo@y.co", "MEMBER")))

    admin = actor(repo, repo.outsider)
    with pytest.raises(ForbiddenError):
        run(handlers.change_role(repo, ChangeRoleCommand(admin, repo.owner, "MEMBER")))
    with pytest.raises(ForbiddenError):
        run(handlers.remove_member(repo, RemoveMemberCommand(admin, repo.owner)))
    with pytest.raises(ForbiddenError):  # un miembro no saca a otros
        run(handlers.remove_member(repo, RemoveMemberCommand(member, repo.outsider)))

    run(handlers.remove_member(repo, RemoveMemberCommand(member, repo.member)))  # pero sí puede salirse
    assert repo.member not in repo.roles
