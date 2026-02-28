"""
Time Decay Algorithm
Reduces risk scores as time passes. Older anomalies matter less.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class TimeDecayCalculator:
    """
    Applies time decay to risk scores.
    
    Formula:
    decayed_risk = risk * (decay_factor ^ age_days)
    
    Where decay_factor = 0.995 per day (0.5% decay)
    """
    
    def __init__(self, decay_factor: float = 0.995, min_risk: float = 0.01):
        """
        Initialize time decay calculator.
        
        Args:
            decay_factor: Decay per day (0.995 = 0.5% per day)
            min_risk: Minimum risk floor (don't go below this)
        """
        self.decay_factor = decay_factor
        self.min_risk = min_risk
        logger.info(f"Time decay: {(1-decay_factor)*100:.1f}% per day")
    
    def apply_decay(self, risk_score: float, last_seen: datetime) -> Tuple[float, float]:
        """
        Apply time decay to a risk score.
        
        Args:
            risk_score: Original risk score (0-1)
            last_seen: Last time this entity was seen
            
        Returns:
            (decayed_risk, age_days)
        """
        now = datetime.utcnow()
        age = now - last_seen
        age_days = max(0, age.total_seconds() / (24 * 3600))
        
        # Apply exponential decay
        decay_multiplier = (self.decay_factor ** age_days)
        decayed_risk = risk_score * decay_multiplier
        decayed_risk = max(self.min_risk, decayed_risk)  # Floor at min
        
        logger.debug(f"Decay: {risk_score:.3f} → {decayed_risk:.3f} (age: {age_days:.1f}d)")
        
        return decayed_risk, age_days
    
    def apply_decay_to_graph(self, graph) -> int:
        """
        Apply time decay to all nodes in graph.
        
        Args:
            graph: GraphStore instance
            
        Returns:
            Number of nodes updated
        """
        updated = 0
        now = datetime.utcnow()
        
        for node_id in list(graph.graph.nodes):
            node = graph.get_node(node_id)
            if not node:
                continue
            
            risk = node.get('risk_score', 0.0)
            last_seen = node.get('last_seen', now)
            
            decayed_risk, _ = self.apply_decay(risk, last_seen)
            
            if decayed_risk != risk:
                graph.update_node_risk(node_id, decayed_risk)
                updated += 1
        
        logger.info(f"Time decay applied to {updated} nodes")
        return updated
    
    def get_age_category(self, last_seen: datetime) -> str:
        """Categorize node age."""
        now = datetime.utcnow()
        age_days = (now - last_seen).total_seconds() / (24 * 3600)
        
        if age_days < 1:
            return "fresh"
        elif age_days < 7:
            return "recent"
        elif age_days < 30:
            return "medium"
        else:
            return "old"
