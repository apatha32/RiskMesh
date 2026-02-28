"""
Tests for Base Risk Calculation module
"""
import pytest
from app.graph.graph_store import GraphStore
from app.risk.base_risk import BaseRiskCalculator


@pytest.fixture
def calculator():
    """Create a base risk calculator."""
    return BaseRiskCalculator()


@pytest.fixture
def graph():
    """Create a fresh graph."""
    return GraphStore()


def test_high_amount_increases_risk(calculator, graph):
    """Test that high transaction amounts increase risk."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 2000.0  # Above threshold
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have risk from high amount
    assert risk >= 0.3


def test_low_amount_no_risk(calculator, graph):
    """Test that low amounts don't trigger amount-based risk."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 50.0  # Below threshold
    }
    
    risk = calculator.calculate(event, graph)
    
    # Risk should be less than 0.3 (no high amount risk)
    assert risk < 0.3


def test_new_device_increases_risk(calculator, graph):
    """Test that new device for user increases risk."""
    event = {
        "user_id": "user_1",
        "device_id": "device_new",  # Not seen before
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 100.0
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have risk from new device
    assert risk >= 0.2


def test_known_device_no_device_risk(calculator, graph):
    """Test that known device doesn't add device risk."""
    # Add edge to indicate device is known
    graph.add_node("user_user_1", "user", 0.0)
    graph.add_node("device_device_1", "device", 0.0)
    graph.add_edge("user_user_1", "device_device_1", weight=0.8)
    
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 100.0
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have less risk (no new device risk)
    assert risk < 0.2


def test_new_ip_increases_risk(calculator, graph):
    """Test that new IP for user increases risk."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "203.0.113.1",  # New IP
        "merchant_id": "merchant_1",
        "transaction_amount": 100.0
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have risk from new IP
    assert risk >= 0.2


def test_new_merchant_increases_risk(calculator, graph):
    """Test that new merchant for card increases risk."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_new",  # New merchant
        "transaction_amount": 100.0
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have risk from new merchant
    assert risk >= 0.1


def test_risk_capped_at_one(calculator, graph):
    """Test that risk is capped at 1.0."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 5000.0  # Very high
    }
    
    risk = calculator.calculate(event, graph)
    
    # Risk should be capped at 1.0
    assert risk <= 1.0


def test_multiple_risk_factors(calculator, graph):
    """Test that multiple risk factors combine."""
    event = {
        "user_id": "user_1",
        "device_id": "device_1",
        "ip_address": "192.168.1.1",
        "merchant_id": "merchant_1",
        "transaction_amount": 2000.0  # High amount
    }
    
    risk = calculator.calculate(event, graph)
    
    # Should have combined risk from high amount + new device + new IP + new merchant
    # 0.3 + 0.2 + 0.2 + 0.1 = 0.8 (or capped at 1.0)
    assert risk >= 0.7
