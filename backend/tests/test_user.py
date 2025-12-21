import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

import pytest

from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_get_users():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)

        params = dict(
            offset=0,
            limit=100
        )

        response = await ac.get("/api/users", params=params, cookies=response.cookies)
        users = response.json()

        assert response.status_code == 200
        assert users


@pytest.mark.asyncio
async def test_get_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = dict(
            username="user@example.com",
            password="Lorser2009!",
        )
        response = await ac.post("/api/auth/login", data=data)

        response = await ac.get("/api/users/me", cookies=response.cookies)
        user = response.json()

        assert response.status_code == 200
        assert user