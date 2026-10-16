from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_roundtrip():
    stored = hash_password("secreta123")
    assert verify_password("secreta123", stored)
    assert not verify_password("otra", stored)


def test_password_salt_is_random():
    assert hash_password("igual") != hash_password("igual")


def test_jwt_roundtrip():
    token = create_access_token("user-1", "biz-1")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["bid"] == "biz-1"


def test_jwt_rejects_tampered_token():
    token = create_access_token("user-1", "biz-1")
    import pytest

    with pytest.raises(ValueError):
        decode_access_token(token + "x")
