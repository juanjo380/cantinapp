"""Hash de contraseñas y tokens JWT usando solo la librería estándar.

Formato de contraseña: pbkdf2_sha256$iteraciones$salt_b64$hash_b64
Token: JWT HS256 con claims sub (id usuario), bid (id negocio), iat, exp.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from app.core.config import get_settings

_PBKDF2_ITERATIONS = 260_000
_ALG = "HS256"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(derived)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), _b64url_decode(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, _b64url_decode(expected))


def create_access_token(subject: str, business_id: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    now = int(time.time())
    expire = now + (expires_minutes or settings.jwt_expire_minutes) * 60
    header = {"alg": _ALG, "typ": "JWT"}
    payload = {"sub": subject, "bid": business_id, "iat": now, "exp": expire}
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signature = hmac.new(
        settings.jwt_secret.encode(), ".".join(segments).encode(), hashlib.sha256
    ).digest()
    segments.append(_b64url_encode(signature))
    return ".".join(segments)


def decode_access_token(token: str) -> dict:
    """Devuelve el payload o lanza ValueError si el token es inválido o expiró."""
    settings = get_settings()
    try:
        header_seg, payload_seg, signature_seg = token.split(".")
    except ValueError as exc:
        raise ValueError("token mal formado") from exc
    expected = hmac.new(
        settings.jwt_secret.encode(), f"{header_seg}.{payload_seg}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(expected, _b64url_decode(signature_seg)):
        raise ValueError("firma inválida")
    payload = json.loads(_b64url_decode(payload_seg))
    if not isinstance(payload, dict) or not payload.get("sub"):
        raise ValueError("token sin sujeto")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expirado")
    return payload
