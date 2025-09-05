"""
Test cases for suggestion endpoint
Following CLAUDE.md testing guidelines
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestSuggestionEndpoint:
    """Test /api/v1/suggest endpoint"""
    
    def test_suggest_endpoint_basic_web_pattern(self):
        """Test endpoint recognizes basic web pattern"""
        request_data = {
            "canvas_elements": [
                {"type": "rectangle", "text": "client app", "id": "client-1"}
            ],
            "context": {"test": True}
        }
        
        response = client.post("/api/v1/suggest", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestion" in data
        assert "reasoning" in data
        assert "reference" in data
        
        # Should suggest web server and database
        if data["suggestion"]:
            assert isinstance(data["suggestion"]["nodes"], list)
            assert isinstance(data["suggestion"]["edges"], list)
    
    def test_suggest_endpoint_empty_canvas(self):
        """Test endpoint with empty canvas"""
        request_data = {
            "canvas_elements": []
        }
        
        response = client.post("/api/v1/suggest", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "reasoning" in data
        # Might return no suggestion for empty canvas
    
    def test_suggest_endpoint_validation_error(self):
        """Test endpoint validation with invalid data"""
        # Missing required field
        response = client.post("/api/v1/suggest", json={})
        assert response.status_code == 422
    
    def test_suggest_endpoint_payload_too_large(self):
        """Test endpoint rejects payload that's too large"""
        # Create canvas with more than 100 elements
        large_elements = [
            {"type": "rectangle", "text": f"element-{i}", "id": f"elem-{i}"}
            for i in range(101)
        ]
        
        request_data = {
            "canvas_elements": large_elements
        }
        
        response = client.post("/api/v1/suggest", json=request_data)
        assert response.status_code == 413  # Request Entity Too Large
    
    def test_suggest_health_endpoint(self):
        """Test suggestion service health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "suggestion_router"
        assert "patterns_loaded" in data


class TestSuggestionService:
    """Test hardcoded suggestion service logic"""
    
    def test_analyze_canvas_detects_client(self):
        """Test canvas analysis detects client elements"""
        from services.suggestion_service import HardcodedSuggestionService
        
        service = HardcodedSuggestionService()
        elements = [
            {"type": "rectangle", "text": "client application"},
            {"type": "rectangle", "text": "user interface"}
        ]
        
        detected = service.analyze_canvas(elements)
        assert "client" in detected
    
    def test_analyze_canvas_detects_database(self):
        """Test canvas analysis detects database elements"""
        from services.suggestion_service import HardcodedSuggestionService
        
        service = HardcodedSuggestionService()
        elements = [
            {"type": "rectangle", "text": "PostgreSQL database"},
            {"type": "rectangle", "text": "DB server"}
        ]
        
        detected = service.analyze_canvas(elements)
        assert "database" in detected
    
    def test_get_suggestion_returns_valid_response(self):
        """Test service returns valid SuggestionResponse"""
        from services.suggestion_service import HardcodedSuggestionService
        from models.schema import SuggestionResponse
        
        service = HardcodedSuggestionService()
        elements = [
            {"type": "rectangle", "text": "client app"}
        ]
        
        response = service.get_suggestion(elements)
        assert isinstance(response, SuggestionResponse)
        assert isinstance(response.reasoning, str)
        assert len(response.reasoning) > 0
    
    def test_get_suggestion_handles_exception(self):
        """Test service handles exceptions gracefully"""
        from services.suggestion_service import HardcodedSuggestionService
        
        service = HardcodedSuggestionService()
        
        # Pass invalid data that might cause exception
        response = service.get_suggestion(None)
        assert response.suggestion is None
        assert "Error analyzing canvas" in response.reasoning
    
    def test_duplicate_detection(self):
        """Test service avoids duplicate suggestions"""
        from services.suggestion_service import HardcodedSuggestionService
        from models.schema import Node, Suggestion, NodeType
        
        service = HardcodedSuggestionService()
        
        # Test _would_duplicate method
        suggestion = Suggestion(
            nodes=[Node(type=NodeType.CACHE, label="Redis", id="cache-1")]
        )
        existing_nodes = ["cache", "database"]
        
        assert service._would_duplicate(suggestion, existing_nodes) == True
        
        existing_nodes = ["webserver", "database"]
        assert service._would_duplicate(suggestion, existing_nodes) == False


@pytest.mark.asyncio
async def test_suggestion_endpoint_async():
    """Test endpoint works with async client"""
    from httpx import AsyncClient
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/suggest",
            json={"canvas_elements": [{"text": "client", "type": "rect"}]}
        )
    assert response.status_code == 200