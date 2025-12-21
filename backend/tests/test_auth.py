import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

import pytest

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.auth.service import AuthService

@pytest.mark.asyncio
async def test_register_and_verify():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            email="user@example.com",
            username="tester",
            password="Lorser2009!"
        )

        response = await ac.post("/api/auth/register", json=data)
        user = response.json()

        assert response.status_code == 201
        assert user['email'] == "user@example.com"

        params = dict(token = AuthService.create_verify_email_token(user["id"]))

        response = await ac.post("/api/auth/verify", params=params)

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)
        tokens = response.json()

        assert response.status_code == 200
        assert tokens["access_token"]
        assert tokens["refresh_token"]


@pytest.mark.asyncio
async def test_login_incorrect_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="",
        )
        response = await ac.post("/api/auth/login", data=data)

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)

        response = await ac.post("/api/auth/refresh", cookies=response.cookies)
        tokens = response.json()

        assert response.status_code == 200
        assert tokens["access_token"]
        assert tokens["refresh_token"]


@pytest.mark.asyncio
async def test_logout():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)

        response = await ac.post("/api/auth/logout", cookies=response.cookies)

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_abort_all():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)

        response = await ac.post("/api/auth/abort", cookies=response.cookies)

        assert response.status_code == 200





