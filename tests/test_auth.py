"""End-to-end API tests for authentication endpoints."""
from __future__ import annotations

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_register_new_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "Password1",
            "role": "patient",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "patient"
    assert data["user"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "password": "Password1",
        "role": "patient",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    creds = {"name": "Carol", "email": "carol@example.com", "password": "Password1", "role": "patient"}
    await client.post("/api/v1/auth/register", json=creds)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "Password1"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    creds = {"name": "Dan", "email": "dan@example.com", "password": "Password1", "role": "patient"}
    await client.post("/api/v1/auth/register", json=creds)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "dan@example.com", "password": "WrongPass9"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": "Password1", "role": "patient"},
    )
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "eve@example.com"
