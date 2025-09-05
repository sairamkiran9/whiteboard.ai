"""
Hardcoded suggestion service for system design patterns
Following CLAUDE.md guidelines for predictable, safe outputs
"""

from typing import Dict, List, Optional
from models.schema import Node, Edge, Suggestion, SuggestionResponse, NodeType, EdgeType


class HardcodedSuggestionService:
    """Service providing hardcoded architectural suggestions"""
    
    def __init__(self):
        self.patterns = {
            "basic_web": {
                "trigger": ["client"],
                "suggestion": Suggestion(
                    nodes=[
                        Node(type=NodeType.WEBSERVER, label="Web Server", id="webserver-1"),
                        Node(type=NodeType.DATABASE, label="Database", id="database-1")
                    ],
                    edges=[
                        Edge(**{"from": "client-1", "to": "webserver-1", "type": EdgeType.REQUESTS})
                    ]
                ),
                "reasoning": "Added web server and database for basic web application architecture",
                "reference": "https://aws.amazon.com/architecture/web-applications/"
            },
            
            "api_gateway_pattern": {
                "trigger": ["webserver", "client"],
                "suggestion": Suggestion(
                    nodes=[
                        Node(type=NodeType.API_GATEWAY, label="API Gateway", id="api-gateway-1")
                    ],
                    edges=[
                        Edge(**{"from": "client-1", "to": "api-gateway-1", "type": EdgeType.REQUESTS}),
                        Edge(**{"from": "api-gateway-1", "to": "webserver-1", "type": EdgeType.REQUESTS})
                    ]
                ),
                "reasoning": "Added API Gateway to manage and secure API requests",
                "reference": "https://microservices.io/patterns/apigateway.html"
            },
            
            "caching_layer": {
                "trigger": ["database", "webserver"],
                "suggestion": Suggestion(
                    nodes=[
                        Node(type=NodeType.CACHE, label="Redis Cache", id="cache-1")
                    ],
                    edges=[
                        Edge(**{"from": "webserver-1", "to": "cache-1", "type": EdgeType.READS_FROM}),
                        Edge(**{"from": "cache-1", "to": "database-1", "type": EdgeType.READS_FROM})
                    ]
                ),
                "reasoning": "Added caching layer to improve database read performance",
                "reference": "https://aws.amazon.com/caching/"
            },
            
            "message_queue": {
                "trigger": ["webserver", "worker"],
                "suggestion": Suggestion(
                    nodes=[
                        Node(type=NodeType.QUEUE, label="Message Queue", id="queue-1")
                    ],
                    edges=[
                        Edge(**{"from": "webserver-1", "to": "queue-1", "type": EdgeType.SENDS_MESSAGE}),
                        Edge(**{"from": "queue-1", "to": "worker-1", "type": EdgeType.SENDS_MESSAGE})
                    ]
                ),
                "reasoning": "Added message queue for asynchronous processing",
                "reference": "https://aws.amazon.com/message-queue/"
            },
            
            "load_balancer": {
                "trigger": ["client", "api-gateway"],
                "suggestion": Suggestion(
                    nodes=[
                        Node(type=NodeType.WEBSERVER, label="Load Balancer", id="load-balancer-1")
                    ],
                    edges=[
                        Edge(**{"from": "client-1", "to": "load-balancer-1", "type": EdgeType.REQUESTS}),
                        Edge(**{"from": "load-balancer-1", "to": "api-gateway-1", "type": EdgeType.REQUESTS})
                    ]
                ),
                "reasoning": "Added load balancer to distribute traffic across multiple instances",
                "reference": "https://aws.amazon.com/elasticloadbalancing/"
            }
        }
    
    def analyze_canvas(self, canvas_elements: List[Dict]) -> List[str]:
        """Extract node types from canvas elements"""
        node_types = []
        for element in canvas_elements:
            # Simple pattern matching - in real implementation, this would be more sophisticated
            element_type = element.get("type", "")
            element_text = element.get("text", "").lower()
            
            # Map canvas elements to our node types
            if "client" in element_text or "user" in element_text:
                node_types.append("client")
            elif "server" in element_text or "api" in element_text:
                node_types.append("webserver")
            elif "database" in element_text or "db" in element_text:
                node_types.append("database")
            elif "cache" in element_text or "redis" in element_text:
                node_types.append("cache")
            elif "queue" in element_text or "message" in element_text:
                node_types.append("queue")
            elif "worker" in element_text or "processor" in element_text:
                node_types.append("worker")
            elif "storage" in element_text or "file" in element_text:
                node_types.append("storage")
            elif "gateway" in element_text:
                node_types.append("api-gateway")
        
        return node_types
    
    def get_suggestion(self, canvas_elements: List[Dict], context: Optional[Dict] = None) -> SuggestionResponse:
        """
        Generate hardcoded suggestion based on canvas analysis
        Following CLAUDE.md pattern matching rules
        """
        try:
            # Analyze current canvas
            detected_nodes = self.analyze_canvas(canvas_elements)
            
            # Find matching pattern
            for pattern_name, pattern_data in self.patterns.items():
                triggers = pattern_data["trigger"]
                
                # Check if any trigger nodes are present
                if any(trigger in detected_nodes for trigger in triggers):
                    # Check if suggestion would be duplicate
                    if not self._would_duplicate(pattern_data["suggestion"], detected_nodes):
                        return SuggestionResponse(
                            suggestion=pattern_data["suggestion"],
                            reasoning=pattern_data["reasoning"],
                            reference=pattern_data["reference"]
                        )
            
            # No appropriate suggestion found
            return SuggestionResponse(
                suggestion=None,
                reasoning="No further suggestions for current architecture",
                reference=None
            )
            
        except Exception as e:
            # Safe fallback as per CLAUDE.md
            return SuggestionResponse(
                suggestion=None,
                reasoning=f"Error analyzing canvas: {str(e)}",
                reference=None
            )
    
    def _would_duplicate(self, suggestion: Suggestion, existing_nodes: List[str]) -> bool:
        """Check if suggestion would create duplicate nodes"""
        for node in suggestion.nodes:
            if node.type.value in existing_nodes:
                return True
        return False