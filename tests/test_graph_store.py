"""
Tests for GraphStore module
"""
import pytest
from app.graph.graph_store import GraphStore


@pytest.fixture
def graph():
    """Create a fresh GraphStore for each test."""
    return GraphStore()


def test_add_node(graph):
    """Test adding a node to the graph."""
    graph.add_node("user_123", "user", risk_score=0.5)
    
    node = graph.get_node("user_123")
    assert node is not None
    assert node["node_type"] == "user"
    assert node["risk_score"] == 0.5


def test_add_multiple_nodes(graph):
    """Test adding multiple nodes."""
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    graph.add_node("ip_192.168.1.1", "ip", 0.0)
    
    assert graph.node_count() == 3


def test_add_edge(graph):
    """Test adding an edge between nodes."""
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    
    graph.add_edge("user_1", "device_1", weight=0.8)
    
    assert graph.edge_count() == 1
    edge = graph.graph["user_1"]["device_1"]
    assert edge["weight"] == 0.8
    assert edge["interaction_count"] == 1


def test_update_edge_increments_count(graph):
    """Test that updating an edge increments interaction count."""
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    
    graph.add_edge("user_1", "device_1", weight=0.8)
    graph.add_edge("user_1", "device_1", weight=0.8)  # Same edge again
    
    edge = graph.graph["user_1"]["device_1"]
    assert edge["interaction_count"] == 2


def test_get_neighbors(graph):
    """Test getting neighbors of a node."""
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    graph.add_node("device_2", "device", 0.0)
    graph.add_node("ip_1", "ip", 0.0)
    
    graph.add_edge("user_1", "device_1")
    graph.add_edge("user_1", "device_2")
    graph.add_edge("device_1", "ip_1")
    
    neighbors_1 = graph.get_neighbors("user_1", depth=1)
    assert len(neighbors_1) == 2
    assert "device_1" in neighbors_1
    assert "device_2" in neighbors_1


def test_get_neighbors_multiple_depths(graph):
    """Test getting neighbors at multiple depths."""
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    graph.add_node("ip_1", "ip", 0.0)
    
    graph.add_edge("user_1", "device_1")
    graph.add_edge("device_1", "ip_1")
    
    neighbors_1 = graph.get_neighbors("user_1", depth=1)
    assert len(neighbors_1) == 1
    assert "device_1" in neighbors_1
    
    neighbors_2 = graph.get_neighbors("user_1", depth=2)
    assert len(neighbors_2) == 2
    assert "device_1" in neighbors_2
    assert "ip_1" in neighbors_2


def test_update_node_risk(graph):
    """Test updating a node's risk score."""
    graph.add_node("user_1", "user", 0.1)
    graph.update_node_risk("user_1", 0.9)
    
    node = graph.get_node("user_1")
    assert node["risk_score"] == 0.9


def test_node_count(graph):
    """Test node count."""
    assert graph.node_count() == 0
    
    graph.add_node("user_1", "user", 0.0)
    assert graph.node_count() == 1
    
    graph.add_node("device_1", "device", 0.0)
    assert graph.node_count() == 2


def test_edge_count(graph):
    """Test edge count."""
    assert graph.edge_count() == 0
    
    graph.add_node("user_1", "user", 0.0)
    graph.add_node("device_1", "device", 0.0)
    graph.add_edge("user_1", "device_1")
    
    assert graph.edge_count() == 1


def test_nonexistent_node(graph):
    """Test getting a nonexistent node returns None."""
    node = graph.get_node("nonexistent")
    assert node is None
