import asyncio
from uuid import uuid4

import pytest

from app.core.exceptions import UnprocessableError
from app.modules.auth.application import handlers
from app.modules.auth.application.commands import RegisterCommand
from app.modules.auth.domain.entities import Business, User


class FakeUsers:
    def __init__(self):
        self.consents = None

    async def get_by_email(self, email):
        return None

    async def add(self, *, business_id, email, password_hash, full_name):
        return User(id=uuid4(), business_id=business_id, email=email, full_name=full_name, is_active=True)

    async def add_consents(self, *, business_id, user_id, version, consents):
        self.consents = (version, consents)


class FakeMemberships:
    def __init__(self):
        self.added = []

    async def add(self, *, business_id, user_id, role):
        self.added.append(role)


class FakeBusinesses:
    async def add(self, name):
        return Business(id=uuid4(), name=name)


def register(users, consents, memberships=None, business_name="Tienda"):
    command = RegisterCommand(business_name=business_name, email="a@b.co", password="secreta123", consents=consents)
    return asyncio.run(handlers.register_user(users, FakeBusinesses(), memberships or FakeMemberships(), command))


def test_register_records_every_document_with_version():
    users, memberships = FakeUsers(), FakeMemberships()
    register(users, {"TERMS": True, "PRIVACY": True}, memberships)
    assert memberships.added == ["OWNER"]  # quien registra es el dueño
    version, consents = users.consents
    assert version == handlers.LEGAL_VERSION
    assert consents == {"TERMS": True, "PRIVACY": True, "ML_ANONYMOUS": False}


def test_register_without_business_creates_only_the_account():
    users, memberships = FakeUsers(), FakeMemberships()
    user, business = register(users, {"TERMS": True, "PRIVACY": True}, memberships, business_name="  ")
    assert business is None and user.business_id is None
    assert memberships.added == []
    assert users.consents is not None  # las autorizaciones se guardan igual


def test_register_rejects_missing_required_consent_before_creating_anything():
    users = FakeUsers()
    with pytest.raises(UnprocessableError):
        register(users, {"TERMS": True, "PRIVACY": False, "ML_ANONYMOUS": True})
    assert users.consents is None
