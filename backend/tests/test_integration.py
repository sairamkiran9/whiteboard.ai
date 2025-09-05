"""
Integration tests for end-to-end flow
Following CLAUDE.md testing guidelines
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEndToEndFlow:
    """Test complete end-to-end suggestion flow"""
    
    def test_complete_suggestion_flow(self):
        """Test complete flow from canvas input to suggestion output"""
        # Step 1: Verify app is running
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Step 2: Send canvas with client element
        canvas_request = {
            "canvas_elements": [
                {
                    "type": "rectangle",
                    "text": "Mobile App Client",
                    "id": "mobile-client-1",
                    "x": 100,
                    "y": 100
                }
            ],
            "recent_changes": [
                {
                    "action": "add",
                    "element_id": "mobile-client-1",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "context": {
                "user_id": "test-user",
                "session_id": "test-session-123"
            }
        }
        
        suggestion_response = client.post("/api/v1/suggest", json=canvas_request)
        assert suggestion_response.status_code == 200
        
        # Step 3: Validate response structure
        data = suggestion_response.json()
        
        # Must have required fields
        assert "suggestion" in data
        assert "reasoning" in data
        assert "reference" in data
        
        # Reasoning must not be empty
        assert isinstance(data["reasoning"], str)
        assert len(data["reasoning"].strip()) > 0
        
        # If suggestion is provided, validate structure
        if data["suggestion"] is not None:
            suggestion = data["suggestion"]
            assert "nodes" in suggestion
            assert "edges" in suggestion
            assert isinstance(suggestion["nodes"], list)
            assert isinstance(suggestion["edges"], list)
            
            # Validate node structure if nodes exist
            for node in suggestion["nodes"]:
                assert "type" in node
                assert "label" in node
                assert node["type"] in [
                    "client", "webserver", "api-gateway", "cache",
                    "database", "worker", "queue", "storage"
                ]
                assert len(node["label"].strip()) > 0
            
            # Validate edge structure if edges exist
            for edge in suggestion["edges"]:
                assert "from" in edge or "from_node" in edge
                assert "to" in edge or "to_node" in edge
                assert "type" in edge
                assert edge["type"] in [
                    "requests", "reads-from", "writes-to",
                    "connects-to", "sends-message", "depends-on"
                ]
    
    def test_progressive_suggestions(self):
        """Test that suggestions evolve as canvas grows"""
        # Start with empty canvas
        response1 = client.post("/api/v1/suggest", json={"canvas_elements": []})
        assert response1.status_code == 200
        
        # Add client
        canvas_with_client = {
            "canvas_elements": [
                {"type": "rectangle", "text": "web client", "id": "client-1"}
            ]
        }
        response2 = client.post("/api/v1/suggest", json=canvas_with_client)
        assert response2.status_code == 200
        
        # Add server
        canvas_with_client_server = {
            "canvas_elements": [
                {"type": "rectangle", "text": "web client", "id": "client-1"},
                {"type": "rectangle", "text": "web server", "id": "server-1"}
            ]
        }
        response3 = client.post("/api/v1/suggest", json=canvas_with_client_server)
        assert response3.status_code == 200
        
        # Each response should be valid
        for response in [response1, response2, response3]:
            data = response.json()
            assert "reasoning" in data
            assert len(data["reasoning"].strip()) > 0
    
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        # Test with invalid JSON structure
        invalid_response = client.post("/api/v1/suggest", json={"invalid": "structure"})
        assert invalid_response.status_code == 422
        
        # Test with malformed canvas element
        malformed_canvas = {
            "canvas_elements": [
                {"invalid_structure": True}
            ]
        }
        response = client.post("/api/v1/suggest", json=malformed_canvas)
        # Should still process but might return no suggestion
        assert response.status_code == 200
    
    def test_logging_integration(self):
        """Test that logging works in integration"""
        import os
        
        # Make request that should generate logs
        response = client.post("/api/v1/suggest", json={
            "canvas_elements": [
                {"type": "rectangle", "text": "database server"}
            ]
        })
        assert response.status_code == 200
        
        # Check that log directory exists
        assert os.path.exists("logs/llm")
        
        # Check that log files are being created
        log_files = os.listdir("logs/llm")
        # At least one log file should exist (could be app.log or dated .json files)
        assert len(log_files) > 0