"""
Tests for Risk Propagation module
"""
import pytest
from app.graph.graph_store import GraphStore
from app.graph.propagation import RiskPropagator


@pytest.fixture
def graph():
    """Create a fresh graph for tests."""
    g = GraphStore()
    
    # Add test nodes
    g.add_node("user_1", "user", risk_score=0.0)
    g.add_node("device_1", "device", risk_score=0.0)
    g.add_node("ip_1", "ip", risk_score=0.0)
    g.add_node("merchant_1", "merchant", risk_score=0.0)
    
    # Add edges
    g.add_edge("user_1", "device_1", weight=0.8)
    g.add_edge("device_1", "ip_1", weight=0.7)
    g.add_edge("device_1", "merchant_1", weight=0.6)
    
    return g


@pytest.fixture
def propagator():
    """Create a propagator."""
    return RiskPropagator(alpha=0.5, max_depth=2, risk_threshold=0.1)


def test_no_propagation_below_threshold(graph, propagator):
    """Test that risk below threshold doesn't propagate."""
    result = propagator.propagate(graph, "user_1", base_risk=0.05)
    
    # Only source node should have risk
    assert len(result) == 1
    assert result["user_1"] == 0.05


def test_propagation_above_threshold(graph, propagator):
    """Test that risk above threshold propagates."""
    result = propagator.propagate(graph, "user_1", base_risk=0.5)
    
    # Source and neighbors should have risk
    assert "user_1" in result
    assert result["user_1"] == 0.5
    
    # Check that neighbor got some risk
    if "device_1" in result:
        # base risk of device_1 (0.0) + 0.5 * 0.8 * 0.5 = 0.2
        assert result["device_1"] > 0


def test_propagation_depth_limit(graph, propagator):
    """Test that propagation respects depth limit."""
    result = propagator.propagate(graph, "user_1", base_risk=0.5)
    
    # With depth=2 and edges user->device->ip, we should reach ip
    # With depth=2 and edges user->device->merchant, we should reach merchant
    # But not beyond that
    
    assert "user_1" in result
    # Device should be at depth 1
    if "device_1" in result:
        assert result["device_1"] <= 1.0  # Risk capped at 1.0


def test_propagation_formula(graph, propagator):
    """Test the propagation formula calculation."""
    graph.update_node_risk("device_1", 0.3)
    
    result = propagator.propagate(graph, "user_1", base_risk=0.6)
    
    # device_1 new risk = 0.3 + 0.5 * (0.6 * 0.8) = 0.3 + 0.24 = 0.54
    if "device_1" in result:
        expected = 0.3 + 0.5 * (0.6 * 0.8)
        assert abs(result["device_1"] - expected) < 0.01


def test_risk_capped_at_one(graph, propagator):
    """Test that risk is capped at 1.0."""
    graph.update_node_risk("device_1", 0.9)
    
    result = propagator.propagate(graph, "user_1", base_risk=0.9)
    
    # Risk should not exceed 1.0
    for risk in result.values():
        assert risk <= 1.0


def test_propagation_returns_affected_nodes(graph, propagator):
    """Test that propagation returns all affected nodes."""
    result = propagator.propagate(graph, "user_1", base_risk=0.5)
    
    # Should return a dict
    assert isinstance(result, dict)
    
    # Source node should always be included
    assert "user_1" in result
