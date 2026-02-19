"""
Base Risk Calculation
"""
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseRiskCalculator:
    """
    Calculates base risk for a transaction based on rules.
    
    Rules:
    - High transaction amount
    - New device for user
    - New IP for user
    - New merchant for card
    """
    
    def __init__(self):
        """Initialize calculator."""
        self.high_amount_threshold = 1000.0
    
    def calculate(self, event: Dict[str, Any], graph) -> float:
        """
        Calculate base risk for transaction.
        
        Rules:
        - High transaction amount: risk += 0.3 if amount > threshold
        - New device for user: risk += 0.2 if first time seeing this device for user
        - New IP for user: risk += 0.2 if first time seeing this IP for user
        - New merchant for card: risk += 0.1 if first time seeing this merchant
        
        Args:
            event: Transaction event with user_id, device_id, ip_address, merchant_id, amount
            graph: GraphStore instance
            
        Returns:
            Base risk score (0-1)
        """
        risk = 0.0
        
        user_id = event.get("user_id")
        device_id = event.get("device_id")
        ip_address = event.get("ip_address")
        merchant_id = event.get("merchant_id")
        amount = event.get("transaction_amount", 0.0)
        
        # Rule 1: High transaction amount
        if amount > self.high_amount_threshold:
            risk += 0.3
            logger.debug(f"High amount detected: ${amount} -> risk += 0.3")
        
        # Rule 2: New device for user
        if user_id and device_id:
            edge_exists = graph.graph.has_edge(f"user_{user_id}", f"device_{device_id}")
            if not edge_exists:
                risk += 0.2
                logger.debug(f"New device for user {user_id} -> risk += 0.2")
        
        # Rule 3: New IP for user
        if user_id and ip_address:
            edge_exists = graph.graph.has_edge(f"user_{user_id}", f"ip_{ip_address}")
            if not edge_exists:
                risk += 0.2
                logger.debug(f"New IP for user {user_id} -> risk += 0.2")
        
        # Rule 4: New merchant for card
        if merchant_id:
            # For MVP, we use card_id as device_id for simplicity
            card_id = device_id  # Treating device as card in MVP
            edge_exists = graph.graph.has_edge(f"card_{card_id}", f"merchant_{merchant_id}")
            if not edge_exists:
                risk += 0.1
                logger.debug(f"New merchant for card {card_id} -> risk += 0.1")
        
        # Cap risk at 1.0
        final_risk = min(risk, 1.0)
        logger.info(f"Base risk calculated: {final_risk:.3f} for event from user {user_id}")
        
        return final_risk
