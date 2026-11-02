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


class FakeBusinesses:
    async def add(self, name):
        return Business(id=uuid4(), name=name)


def register(users, consents):
    command = RegisterCommand(business_name="Tienda", email="a@b.co", password="secreta123", consents=consents)
    return asyncio.run(handlers.register_user(users, FakeBusinesses(), command))


def test_register_records_every_document_with_version():
    users = FakeUsers()
    register(users, {"TERMS": True, "PRIVACY": True, "COOKIES": True})
    version, consents = users.consents
    assert version == handlers.LEGAL_VERSION
    assert consents == {"TERMS": True, "PRIVACY": True, "COOKIES": True, "ML_ANONYMOUS": False}


def test_register_rejects_missing_required_consent_before_creating_anything():
    users = FakeUsers()
    with pytest.raises(UnprocessableError):
        register(users, {"TERMS": True, "PRIVACY": True, "COOKIES": False, "ML_ANONYMOUS": True})
    assert users.consents is None
