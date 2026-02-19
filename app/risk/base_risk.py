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
        
        Args:
            event: Transaction event with user_id, device_id, ip_address, merchant_id, amount
            graph: GraphStore instance
            
        Returns:
            Base risk score (0-1)
        """
        pass
