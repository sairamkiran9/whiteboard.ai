"""
Test cases for main FastAPI application
Following CLAUDE.md testing guidelines
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI System Design Copilot API"
    assert data["status"] == "running"
    assert data["version"] == "0.1.0"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are present"""
    response = client.get("/")
    assert response.status_code == 200
    # CORS headers should be present for frontend integration