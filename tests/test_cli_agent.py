import pytest
import importlib.util
from pathlib import Path
import httpx

# Dynamically load api.py
api_path = Path(__file__).parents[1] / "api.py"
spec = importlib.util.spec_from_file_location("api", api_path)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

@pytest.mark.asyncio
async def test_workspace_info():
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/workspace_info")
    assert response.status_code == 200
    assert "workspace_exists" in response.json()

@pytest.mark.asyncio
async def test_create_query_and_get_result():
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/query", json={"text": "Test deployment query"})
        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "processing"

        query_id = data["query_id"]

        # Fetch result
        result_response = await ac.get(f"/result/{query_id}")
        assert result_response.status_code == 200
        assert "status" in result_response.json()

@pytest.mark.asyncio
async def test_reset_workspace():
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/reset_workspace")
    assert response.status_code == 200
    assert response.json()["status"] in ["success", "error"]
