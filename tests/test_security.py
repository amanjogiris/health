"""Unit tests for core security utilities."""
from __future__ import annotations

import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_and_verify():
    plain = "SecurePass1"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_verify_wrong_password():
    hashed = hash_password("CorrectPass1")
    assert not verify_password("WrongPass1", hashed)


def test_create_and_decode_token():
    token = create_access_token(user_id=42, role="patient")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "patient"


def test_decode_invalid_token():
    import jwt

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("this.is.invalid")
