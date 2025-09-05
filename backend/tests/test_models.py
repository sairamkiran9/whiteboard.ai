"""
Test cases for Pydantic models
Following CLAUDE.md testing guidelines
"""

import pytest
from pydantic import ValidationError

from models.schema import (
    Node, Edge, Suggestion, SuggestionResponse, CanvasRequest,
    NodeType, EdgeType
)


class TestNodeModel:
    """Test Node model validation"""
    
    def test_valid_node_creation(self):
        """Test creating a valid node"""
        node = Node(type=NodeType.DATABASE, label="PostgreSQL DB", id="db-1")
        assert node.type == NodeType.DATABASE
        assert node.label == "PostgreSQL DB"
        assert node.id == "db-1"
    
    def test_node_label_validation(self):
        """Test node label validation rules"""
        # Valid label
        node = Node(type=NodeType.CACHE, label="Redis Cache")
        assert node.label == "Redis Cache"
        
        # Empty label should fail
        with pytest.raises(ValidationError):
            Node(type=NodeType.CACHE, label="")
        
        # Whitespace-only label should fail
        with pytest.raises(ValidationError):
            Node(type=NodeType.CACHE, label="   ")
        
        # Label trimming
        node = Node(type=NodeType.CACHE, label="  Redis Cache  ")
        assert node.label == "Redis Cache"
    
    def test_invalid_node_type(self):
        """Test invalid node type rejection"""
        with pytest.raises(ValidationError):
            Node(type="invalid-type", label="Test")


class TestEdgeModel:
    """Test Edge model validation"""
    
    def test_valid_edge_creation(self):
        """Test creating a valid edge"""
        edge = Edge(**{"from": "client-1", "to": "server-1", "type": EdgeType.REQUESTS})
        assert edge.from_node == "client-1"
        assert edge.to_node == "server-1" 
        assert edge.type == EdgeType.REQUESTS
    
    def test_edge_alias_support(self):
        """Test edge supports 'from' and 'to' aliases"""
        # Using alias names
        edge = Edge(**{"from": "client-1", "to": "server-1", "type": EdgeType.REQUESTS})
        assert edge.from_node == "client-1"
        assert edge.to_node == "server-1"
    
    def test_invalid_edge_type(self):
        """Test invalid edge type rejection"""
        with pytest.raises(ValidationError):
            Edge(**{"from": "a", "to": "b", "type": "invalid-type"})


class TestSuggestionModel:
    """Test Suggestion model validation"""
    
    def test_valid_suggestion(self):
        """Test creating a valid suggestion"""
        nodes = [
            Node(type=NodeType.CACHE, label="Redis Cache", id="cache-1"),
            Node(type=NodeType.DATABASE, label="PostgreSQL", id="db-1")
        ]
        edges = [
            Edge(**{"from": "cache-1", "to": "db-1", "type": EdgeType.READS_FROM})
        ]
        
        suggestion = Suggestion(nodes=nodes, edges=edges)
        assert len(suggestion.nodes) == 2
        assert len(suggestion.edges) == 1
    
    def test_suggestion_limits(self):
        """Test suggestion enforces CLAUDE.md limits (max 2 nodes/edges)"""
        # Too many nodes should fail
        nodes = [
            Node(type=NodeType.CACHE, label="Cache 1", id="cache-1"),
            Node(type=NodeType.DATABASE, label="DB 1", id="db-1"),
            Node(type=NodeType.QUEUE, label="Queue 1", id="queue-1")
        ]
        with pytest.raises(ValidationError):
            Suggestion(nodes=nodes, edges=[])
        
        # Too many edges should fail
        edges = [
            Edge(**{"from": "a", "to": "b", "type": EdgeType.REQUESTS}),
            Edge(**{"from": "b", "to": "c", "type": EdgeType.READS_FROM}),
            Edge(**{"from": "c", "to": "d", "type": EdgeType.WRITES_TO})
        ]
        with pytest.raises(ValidationError):
            Suggestion(nodes=[], edges=edges)
    
    def test_empty_suggestion(self):
        """Test empty suggestion is valid"""
        suggestion = Suggestion()
        assert len(suggestion.nodes) == 0
        assert len(suggestion.edges) == 0


class TestSuggestionResponseModel:
    """Test SuggestionResponse model validation"""
    
    def test_valid_response_with_suggestion(self):
        """Test valid response with suggestion"""
        suggestion = Suggestion(
            nodes=[Node(type=NodeType.CACHE, label="Redis", id="cache-1")],
            edges=[]
        )
        
        response = SuggestionResponse(
            suggestion=suggestion,
            reasoning="Added cache for better performance",
            reference="https://redis.io/docs"
        )
        
        assert response.suggestion is not None
        assert response.reasoning == "Added cache for better performance"
        assert response.reference == "https://redis.io/docs"
    
    def test_valid_response_no_suggestion(self):
        """Test valid response with no suggestion (following CLAUDE.md)"""
        response = SuggestionResponse(
            suggestion=None,
            reasoning="No further suggestions",
            reference=None
        )
        
        assert response.suggestion is None
        assert response.reasoning == "No further suggestions"
        assert response.reference is None
    
    def test_empty_reasoning_fails(self):
        """Test empty reasoning validation"""
        with pytest.raises(ValidationError):
            SuggestionResponse(
                suggestion=None,
                reasoning="",
                reference=None
            )
        
        with pytest.raises(ValidationError):
            SuggestionResponse(
                suggestion=None,
                reasoning="   ",
                reference=None
            )


class TestCanvasRequestModel:
    """Test CanvasRequest model validation"""
    
    def test_valid_canvas_request(self):
        """Test valid canvas request"""
        request = CanvasRequest(
            canvas_elements=[
                {"type": "rectangle", "text": "Web Server", "id": "rect-1"},
                {"type": "arrow", "from": "rect-1", "to": "rect-2"}
            ],
            recent_changes=[
                {"action": "add", "element_id": "rect-1"}
            ],
            context={"user": "test", "session": "123"}
        )
        
        assert len(request.canvas_elements) == 2
        assert len(request.recent_changes) == 1
        assert request.context["user"] == "test"
    
    def test_minimal_canvas_request(self):
        """Test minimal valid canvas request"""
        request = CanvasRequest(canvas_elements=[])
        assert len(request.canvas_elements) == 0
        assert request.recent_changes is None
        assert request.context is None