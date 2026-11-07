import asyncio
from datetime import UTC, datetime, timedelta
from html import escape
from uuid import uuid4

import pytest

from app.core.exceptions import UnprocessableError
from app.core.mailer import invitation_email
from app.core.security import MAX_CODE_ATTEMPTS, verify_password
from app.modules.auth.application import handlers
from app.modules.auth.application.commands import RequestPasswordResetCommand, ResetPasswordCommand
from app.modules.auth.domain.entities import EmailCode, User


class FakeUsers:
    def __init__(self):
        self.user = User(id=uuid4(), business_id=None, email="a@b.co", full_name="Ana", is_active=True)
        self.codes: list[EmailCode] = []
        self.password_hash = None

    async def get_by_email(self, email):
        return self.user if email == self.user.email else None

    async def add_code(self, *, user_id, purpose, code_hash, expires_at):
        self.codes.append(EmailCode(uuid4(), code_hash, 0, expires_at, datetime.now(UTC)))

    async def latest_code(self, user_id, purpose):
        return self.codes[-1] if self.codes else None

    async def count_code_attempt(self, code_id):
        self.codes[-1].attempts += 1

    async def use_code(self, code_id):
        self.codes[-1].used_at = datetime.now(UTC)

    async def set_password(self, user_id, password_hash):
        self.password_hash = password_hash


def run(coro):
    return asyncio.run(coro)


def ask(users, email="a@b.co"):
    return run(handlers.request_password_reset(users, RequestPasswordResetCommand(email)))


def reset(users, code, password="nueva-clave-1"):
    return run(handlers.reset_password(users, ResetPasswordCommand("a@b.co", code, password)))


def test_unknown_email_and_quick_resend_send_nothing():
    users = FakeUsers()
    assert ask(users, "nadie@b.co") is None
    code = ask(users)
    assert len(code) == 6 and code.isdigit()
    assert ask(users) is None  # antes de RESET_RESEND_SECONDS sigue valiendo el primero
    users.codes[-1].created_at -= timedelta(seconds=handlers.RESET_RESEND_SECONDS)
    assert ask(users) is not None


def test_code_resets_password_once():
    users = FakeUsers()
    code = ask(users)
    handlers._failed_logins["a@b.co"] = [0.0]
    reset(users, code)
    assert verify_password("nueva-clave-1", users.password_hash)
    assert "a@b.co" not in handlers._failed_logins  # desbloquea el login
    with pytest.raises(UnprocessableError):
        reset(users, code)  # un solo uso


def test_wrong_codes_burn_the_code_and_expiry_applies():
    users = FakeUsers()
    code = ask(users)
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"
    for _ in range(MAX_CODE_ATTEMPTS):
        with pytest.raises(UnprocessableError):
            reset(users, wrong)
    with pytest.raises(UnprocessableError):
        reset(users, code)  # ni el correcto sirve tras agotar los intentos
    assert users.password_hash is None

    users = FakeUsers()
    code = ask(users)
    users.codes[-1].expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(UnprocessableError):
        reset(users, code)


def test_invitation_email_escapes_user_text():
    _, _, html = invitation_email('<a href="x">Tienda</a>', "miembro", "<b>Eva</b>", "https://app/i?t=1", 48)
    assert "<b>Eva</b>" not in html and escape("<b>Eva</b>") in html
    assert '<a href="x">' not in html
