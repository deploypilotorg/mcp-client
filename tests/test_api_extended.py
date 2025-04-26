import pytest
import importlib.util
from pathlib import Path
import httpx
import os
import asyncio

# Dynamically load api.py
api_path = Path(__file__).parents[1] / "api.py"
spec = importlib.util.spec_from_file_location("api", api_path)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

@pytest.mark.asyncio
async def test_workspace_info_has_files():
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/workspace_info")
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_exists"] is True
    assert isinstance(data["files"], list)

@pytest.mark.asyncio
async def test_invalid_result_lookup():
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/result/invalid_id_123")
    assert response.status_code == 200
    assert response.json() == {"status": "not_found"}

@pytest.mark.asyncio
async def test_missing_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    await api.run_agent("test_001", "Deploy something")
    assert api.active_tasks["test_001"]["status"] == "error"
    assert "not found in .env file" in api.active_tasks["test_001"]["result"]
