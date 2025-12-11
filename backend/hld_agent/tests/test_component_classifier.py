"""
Tests for ComponentClassifier
"""
import pytest
from hld_agent.utils.component_classifier import ComponentClassifier


class TestComponentClassifier:
    """Test component name classification"""

    def test_classify_exact_matches(self):
        """Test exact name matches"""
        classifier = ComponentClassifier()

        assert classifier.classify("user") == "client"
        assert classifier.classify("API Gateway") == "api-gateway"
        assert classifier.classify("redis") == "cache"
        assert classifier.classify("postgres") == "database"
        assert classifier.classify("kafka") == "queue"

    def test_classify_case_insensitive(self):
        """Test case-insensitive classification"""
        classifier = ComponentClassifier()

        assert classifier.classify("USER") == "client"
        assert classifier.classify("Api Gateway") == "api-gateway"
        assert classifier.classify("REDIS") == "cache"

    def test_classify_partial_matches(self):
        """Test partial keyword matching"""
        classifier = ComponentClassifier()

        assert classifier.classify("API GW") == "api-gateway"
        assert classifier.classify("Load Balancer") == "load-balancer"
        assert classifier.classify("PostgreSQL Database") == "database"
        assert classifier.classify("Message Queue") == "queue"
        assert classifier.classify("job worker") == "worker"

    def test_classify_pattern_based(self):
        """Test pattern-based classification"""
        classifier = ComponentClassifier()

        assert classifier.classify("mysql-primary") == "database"
        assert classifier.classify("redis-cluster") == "cache"
        assert classifier.classify("auth-service") == "auth"
        assert classifier.classify("monitoring-stack") == "monitoring"

    def test_classify_unknown_defaults_to_service(self):
        """Test that unknown components default to 'service'"""
        classifier = ComponentClassifier()

        assert classifier.classify("unknown-component") == "service"
        assert classifier.classify("my-app") == "service"
        assert classifier.classify("") == "service"

    def test_get_type_description(self):
        """Test getting human-readable descriptions"""
        classifier = ComponentClassifier()

        desc = classifier.get_type_description("api-gateway")
        assert "API gateway" in desc
        assert "routing" in desc or "authentication" in desc

        desc = classifier.get_type_description("database")
        assert "Database" in desc or "storage" in desc

    def test_classify_real_world_names(self):
        """Test with real-world component names"""
        classifier = ComponentClassifier()

        # Common real-world names
        assert classifier.classify("nginx") == "load-balancer"
        assert classifier.classify("Kong Gateway") == "api-gateway"
        assert classifier.classify("MongoDB") == "database"
        assert classifier.classify("RabbitMQ") == "queue"
        assert classifier.classify("Lambda Function") == "worker"
        assert classifier.classify("S3 Bucket") == "storage"
        assert classifier.classify("OAuth Server") == "auth"
        assert classifier.classify("Prometheus") == "monitoring"
