"""
Component type classifier - Maps user-drawn component names to standard types
"""
from typing import Dict, List
import re


class ComponentClassifier:
    """Classifies component names into standard architecture types"""

    # Component type taxonomy with aliases
    COMPONENT_TYPES: Dict[str, List[str]] = {
        "client": ["user", "browser", "mobile", "frontend", "client", "ui", "web app"],
        "load-balancer": ["load balancer", "lb", "nginx", "haproxy", "alb", "elb"],
        "api-gateway": ["api gateway", "gateway", "api gw", "kong", "apigee"],
        "service": ["service", "microservice", "api", "backend", "server", "app"],
        "cache": ["cache", "redis", "memcached", "elasticache", "caching"],
        "database": ["database", "db", "postgres", "postgresql", "mysql", "mongodb", "dynamo", "rds"],
        "queue": ["queue", "message queue", "kafka", "rabbitmq", "sqs", "mq", "broker"],
        "worker": ["worker", "job worker", "consumer", "processor", "lambda"],
        "storage": ["storage", "s3", "blob", "file storage", "object storage", "cdn"],
        "auth": ["auth", "authentication", "oauth", "identity", "sso", "login"],
        "monitoring": ["monitoring", "logs", "metrics", "prometheus", "grafana", "cloudwatch"],
        "network": ["vpn", "firewall", "nat", "subnet", "vpc", "network"],
    }

    @classmethod
    def classify(cls, component_name: str) -> str:
        """
        Classify a component name into a standard type

        Args:
            component_name: User-provided component name (e.g., "API Gateway", "postgres")

        Returns:
            Standard component type (e.g., "api-gateway", "database")
        """
        if not component_name:
            return "service"  # Default fallback

        # Normalize name
        normalized = component_name.lower().strip()

        # Direct match
        for comp_type, aliases in cls.COMPONENT_TYPES.items():
            if normalized in aliases:
                return comp_type

        # Partial match (contains keyword)
        for comp_type, aliases in cls.COMPONENT_TYPES.items():
            for alias in aliases:
                if alias in normalized or normalized in alias:
                    return comp_type

        # Pattern-based classification
        if re.search(r"(api|gateway|gw)", normalized):
            return "api-gateway"
        if re.search(r"(db|database|sql|mongo|dynamo)", normalized):
            return "database"
        if re.search(r"(cache|redis|mem)", normalized):
            return "cache"
        if re.search(r"(queue|kafka|rabbit|sqs)", normalized):
            return "queue"
        if re.search(r"(worker|lambda|function)", normalized):
            return "worker"
        if re.search(r"(storage|s3|blob|cdn)", normalized):
            return "storage"
        if re.search(r"(auth|login|oauth|sso)", normalized):
            return "auth"
        if re.search(r"(monitor|log|metric|observ)", normalized):
            return "monitoring"
        if re.search(r"(load|balance|lb|nginx)", normalized):
            return "load-balancer"

        # Default: treat as generic service
        return "service"

    @classmethod
    def get_type_description(cls, component_type: str) -> str:
        """Get a human-readable description of a component type"""
        descriptions = {
            "client": "User-facing client (browser, mobile app, etc.)",
            "load-balancer": "Load balancer for distributing traffic",
            "api-gateway": "API gateway for routing and authentication",
            "service": "Application service or microservice",
            "cache": "Caching layer (Redis, Memcached)",
            "database": "Database for persistent storage",
            "queue": "Message queue for async communication",
            "worker": "Background worker or job processor",
            "storage": "Object/file storage (S3, blob storage)",
            "auth": "Authentication and authorization service",
            "monitoring": "Monitoring and observability stack",
            "network": "Network infrastructure component",
        }
        return descriptions.get(component_type, "Generic component")
