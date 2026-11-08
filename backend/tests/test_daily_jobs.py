"""Trabajo diario: autenticación del endpoint, un correo por día y aislamiento entre negocios."""
import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.mailer import alerts_digest_email
from app.modules.jobs.api import router as jobs_api
from app.modules.jobs.application.daily import run_daily_jobs
from app.modules.jobs.domain.policy import should_send_digest

SECRET = "s" * 40
NOW = datetime(2026, 11, 8, 11, 0, tzinfo=UTC)


def _call_endpoint(monkeypatch, header, configured=SecretStr(SECRET)):
    ran = []

    async def fake_jobs():
        ran.append(True)
        return [{"business_id": "x", "ok": True}]

    monkeypatch.setattr(jobs_api, "run_daily_jobs", fake_jobs)
    monkeypatch.setattr(jobs_api, "get_settings", lambda: SimpleNamespace(cron_secret=configured))
    return asyncio.run(jobs_api.daily(x_cron_secret=header)), ran


def test_endpoint_requires_the_cron_secret(monkeypatch):
    # AppError.status_code es el HTTP que devuelve la API (shared/api/error_handlers.py)
    with pytest.raises(UnauthorizedError):
        _call_endpoint(monkeypatch, None)
    with pytest.raises(ForbiddenError):
        _call_endpoint(monkeypatch, "otro")
    body, ran = _call_endpoint(monkeypatch, SECRET)
    assert ran and body["failed"] == 0


def test_endpoint_is_closed_when_no_secret_is_configured(monkeypatch):
    with pytest.raises(ForbiddenError):
        _call_endpoint(monkeypatch, "lo-que-sea", configured=None)


def test_cron_secret_is_mandatory_outside_development():
    base = {"db_host": "h", "db_user": "u", "db_password": "p", "jwt_secret": "j" * 40, "environment": "production"}
    with pytest.raises(ValidationError):
        Settings(**base)
    with pytest.raises(ValidationError):
        Settings(**base, cron_secret="corto")
    assert Settings(**base, cron_secret=f" {SECRET}\n").cron_secret.get_secret_value() == SECRET


def test_digest_only_with_new_alerts_and_once_per_day():
    assert not should_send_digest([], None, NOW)
    assert should_send_digest(["a"], None, NOW)
    assert not should_send_digest(["a"], NOW - timedelta(hours=3), NOW)  # ya se envió hoy
    assert should_send_digest(["a"], NOW - timedelta(days=1), NOW)


def test_one_failing_business_does_not_stop_the_others():
    ok_id, bad_id = uuid4(), uuid4()

    async def run_one(business_id):
        if business_id == bad_id:
            raise RuntimeError("BD caída")
        return {"created": 1}

    results = asyncio.run(run_daily_jobs([bad_id, ok_id], run_one=run_one))
    assert [(r["business_id"], r["ok"]) for r in results] == [(str(bad_id), False), (str(ok_id), True)]
    assert results[0]["error"] == "RuntimeError" and results[1]["created"] == 1


def test_digest_email_escapes_names_and_lists_every_product():
    subject, text, html = alerts_digest_email(
        "<b>Tienda</b>", [("Pan", 0, 5, 12), ("Leche", 2, 6, None)], "https://app/alertas"
    )
    assert subject.endswith("2 productos por reabastecer")
    assert "Pan: agotado; sugerimos comprar 12" in text and "Leche: quedan 2 (mínimo 6)" in text
    assert "<b>Tienda</b>" not in html
