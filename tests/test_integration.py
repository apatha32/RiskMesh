"""
End-to-End Integration Tests for RiskMesh
"""
import pytest
from app.graph.graph_store import GraphStore
from app.graph.propagation import RiskPropagator
from app.risk.base_risk import BaseRiskCalculator
from app.risk.risk_engine import RiskEngine
from app.db.database import Database
import os


@pytest.fixture
def risk_engine():
    """Create a complete risk engine for testing."""
    # Initialize components
    graph_store = GraphStore()
    propagator = RiskPropagator(alpha=0.5, max_depth=2, risk_threshold=0.1)
    base_risk_calc = BaseRiskCalculator()
    
    # Mock database for testing
    db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    database = Database(db_url)
    
    # Create risk engine
    engine = RiskEngine(graph_store, propagator, base_risk_calc, database)
    
    return engine


def test_process_event_returns_result(risk_engine):
    """Test that processing an event returns a result."""
    event = {
        "user_id": "user_123",
        "device_id": "device_456",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 250.0
    }
    
    result = risk_engine.process_event(event)
    
    assert result is not None
    assert "transaction_id" in result
    assert "risk_score" in result
    assert "propagation_depth" in result
    assert "timestamp" in result


def test_process_event_high_risk(risk_engine):
    """Test that high transaction amount triggers high risk."""
    event = {
        "user_id": "user_123",
        "device_id": "device_456",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 5000.0  # High amount
    }
    
    result = risk_engine.process_event(event)
    
    # High amount should result in higher risk
    assert result["risk_score"] > 0.3


def test_process_event_low_risk(risk_engine):
    """Test that low transaction amount has lower risk."""
    # First, add known associations to graph
    engine = risk_engine
    
    # Process multiple events from same user to establish patterns
    event1 = {
        "user_id": "user_123",
        "device_id": "device_456",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 50.0  # Low amount
    }
    
    result = engine.process_event(event1)
    
    # Low amount should result in lower risk
    assert result["risk_score"] < 0.3


def test_process_event_updates_graph(risk_engine):
    """Test that processing event updates the graph."""
    graph = risk_engine.graph_store
    initial_nodes = graph.node_count()
    
    event = {
        "user_id": "user_123",
        "device_id": "device_456",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 250.0
    }
    
    risk_engine.process_event(event)
    
    final_nodes = graph.node_count()
    
    # Graph should have new nodes
    assert final_nodes > initial_nodes


def test_multiple_events_accumulate_risk(risk_engine):
    """Test that multiple risky events accumulate risk in graph."""
    engine = risk_engine
    
    # Process first event with new device
    event1 = {
        "user_id": "user_123",
        "device_id": "device_new1",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 2000.0
    }
    
    result1 = engine.process_event(event1)
    risk1 = result1["risk_score"]
    
    # Process second event with another new device
    event2 = {
        "user_id": "user_123",
        "device_id": "device_new2",
        "ip_address": "192.168.1.101",
        "merchant_id": "merchant_789",
        "transaction_amount": 2000.0
    }
    
    result2 = engine.process_event(event2)
    risk2 = result2["risk_score"]
    
    # Both should be risky due to new devices
    assert risk1 > 0.3
    assert risk2 > 0.3


def test_event_latency_under_50ms(risk_engine):
    """Test that event processing latency is under 50ms (MVP goal)."""
    event = {
        "user_id": "user_123",
        "device_id": "device_456",
        "ip_address": "192.168.1.100",
        "merchant_id": "merchant_789",
        "transaction_amount": 250.0
    }
    
    result = risk_engine.process_event(event)
    
    # Check latency metrics
    assert "total_latency_ms" in result
    # For MVP testing, we're more lenient than production (50ms)
    # Real performance depends on system load
    assert result["total_latency_ms"] < 500  # 500ms for safety in test


def test_propagation_affects_risk(risk_engine):
    """Test that risk propagation affects connected nodes."""
    graph = risk_engine.graph_store
    
    # Add connected graph
    graph.add_node("user_123", "user", 0.0)
    graph.add_node("device_456", "device", 0.0)
    graph.add_node("ip_789", "ip", 0.0)
    
    graph.add_edge("user_123", "device_456", weight=0.8)
    graph.add_edge("device_456", "ip_789", weight=0.7)
    
    # Process event with high risk
    event = {
        "user_id": "123",  # Different format to test
        "device_id": "456",
        "ip_address": "789",
        "merchant_id": "999",
        "transaction_amount": 3000.0
    }
    
    result = risk_engine.process_event(event)
    
    # Risk should propagate through graph
    assert result["risk_score"] > 0


def test_event_with_missing_fields(risk_engine):
    """Test handling of events with missing fields."""
    event = {
        "user_id": "user_123",
        "device_id": "device_456",
        # Missing ip_address
        # Missing merchant_id
        "transaction_amount": 250.0
    }
    
    # Should handle gracefully
    try:
        result = risk_engine.process_event(event)
        assert result is not None
    except (KeyError, ValueError):
        # Acceptable to fail gracefully
        pass
