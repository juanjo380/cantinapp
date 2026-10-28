import asyncio
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import TooManyRequestsError, UnauthorizedError
from app.core.security import hash_password
from app.modules.auth.application import handlers
from app.modules.auth.application.commands import LoginCommand
from app.modules.auth.domain.entities import User


class FakeUsers:
    def __init__(self, password: str):
        self.user = User(id=uuid4(), business_id=uuid4(), email="a@b.co", full_name=None, is_active=True)
        self.hash = hash_password(password)

    async def get_credentials(self, email):
        return (self.user, self.hash) if email == self.user.email else None


@pytest.fixture(autouse=True)
def _reset_failures():
    handlers._failed_logins.clear()


def login(users, email, password):
    return asyncio.run(handlers.authenticate(users, LoginCommand(email=email, password=password)))


def test_login_ok_and_wrong_password():
    users = FakeUsers("secreta123")
    assert login(users, "A@b.co", "secreta123").email == "a@b.co"
    with pytest.raises(UnauthorizedError):
        login(users, "a@b.co", "mala")
    with pytest.raises(UnauthorizedError):
        login(users, "nadie@b.co", "x")


def test_lockout_after_repeated_failures_and_success_resets():
    users = FakeUsers("secreta123")
    for _ in range(handlers._MAX_FAILED_LOGINS - 1):
        with pytest.raises(UnauthorizedError):
            login(users, "a@b.co", "mala")
    login(users, "a@b.co", "secreta123")  # un acierto limpia el contador
    for _ in range(handlers._MAX_FAILED_LOGINS):
        with pytest.raises(UnauthorizedError):
            login(users, "a@b.co", "mala")
    with pytest.raises(TooManyRequestsError):
        login(users, "a@b.co", "secreta123")


def test_default_jwt_secret_rejected_outside_development():
    base = {"db_host": "h", "db_user": "u", "db_password": "p"}
    with pytest.raises(ValueError):
        Settings(**base, environment="production", jwt_secret="dev-secret-change-me")
    assert Settings(**base, environment="production", jwt_secret="x" * 32).jwt_secret == "x" * 32
