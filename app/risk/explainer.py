"""
Risk Score Explainability
Explains WHY a risk score was calculated
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RiskExplainer:
    """
    Generates explanations for risk scores.
    
    Explains:
    - Which rules triggered (base risk)
    - Which neighbors propagated risk
    - Clustering impact
    - Historical context
    """
    
    def __init__(self):
        """Initialize explainer."""
        pass
    
    def explain_base_risk(self, event: Dict[str, Any], base_risk: Dict[str, float]) -> Dict[str, Any]:
        """
        Explain base risk components.
        
        Args:
            event: Transaction event
            base_risk: Dict with individual risk components
            
        Returns:
            Explanation dict
        """
        explanation = {
            "rules_triggered": [],
            "total_base_risk": 0.0
        }
        
        # Map components to readable rules
        rule_map = {
            "high_amount": {
                "name": "High Transaction Amount",
                "description": f"Transaction amount ${event.get('transaction_amount', 0):.2f} exceeds threshold"
            },
            "new_device": {
                "name": "New Device",
                "description": f"Device '{event.get('device_id')}' not seen before for this user"
            },
            "new_ip": {
                "name": "New IP Address",
                "description": f"IP '{event.get('ip_address')}' not seen before for this user"
            },
            "new_merchant": {
                "name": "New Merchant",
                "description": f"Merchant '{event.get('merchant_id')}' not previously used"
            }
        }
        
        total = 0.0
        for rule, risk_val in base_risk.items():
            if risk_val > 0:
                rule_info = rule_map.get(rule, {"name": rule, "description": "Unknown rule"})
                explanation["rules_triggered"].append({
                    "rule": rule_info["name"],
                    "risk_contribution": round(risk_val, 3),
                    "description": rule_info["description"]
                })
                total += risk_val
        
        explanation["total_base_risk"] = round(min(total, 1.0), 3)
        return explanation
    
    def explain_propagation(self, propagation_results: Dict[str, float], source_node: str) -> Dict[str, Any]:
        """
        Explain risk propagation.
        
        Args:
            propagation_results: Dict of node -> risk from propagation
            source_node: Original source node
            
        Returns:
            Propagation explanation
        """
        explanation = {
            "source": source_node,
            "propagated_to": [],
            "propagation_distance": 0,
            "total_nodes_affected": len(propagation_results)
        }
        
        # Sort by risk impact (descending)
        sorted_nodes = sorted(
            [(n, r) for n, r in propagation_results.items() if n != source_node],
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5
        
        for node_id, risk in sorted_nodes:
            explanation["propagated_to"].append({
                "node": node_id,
                "risk": round(risk, 3),
                "is_high_risk": risk > 0.6
            })
        
        return explanation
    
    def explain_clustering(self, clusters: Dict[str, List]) -> Dict[str, Any]:
        """
        Explain clustering impact.
        
        Args:
            clusters: Clustering detection results
            
        Returns:
            Clustering explanation
        """
        explanation = {
            "fraud_ring_detected": False,
            "cluster_info": None,
            "risk_boost": 0.0
        }
        
        total_rings = len(clusters.get("rings", []))
        total_stars = len(clusters.get("stars", []))
        total_dense = len(clusters.get("dense_clusters", []))
        
        if total_rings > 0:
            explanation["fraud_ring_detected"] = True
            largest_ring = max(clusters["rings"], key=lambda x: x["size"])
            explanation["cluster_info"] = {
                "type": "fraud_ring",
                "size": largest_ring["size"],
                "avg_risk": largest_ring["avg_risk"]
            }
            explanation["risk_boost"] = 0.2  # Standard boost
        elif total_stars > 0:
            explanation["fraud_ring_detected"] = True
            star = clusters["stars"][0]
            explanation["cluster_info"] = {
                "type": "star_pattern",
                "center": star["center"],
                "branches": star["branches"]
            }
            explanation["risk_boost"] = 0.15
        elif total_dense > 0:
            explanation["fraud_ring_detected"] = True
            cluster = clusters["dense_clusters"][0]
            explanation["cluster_info"] = {
                "type": "dense_cluster",
                "size": cluster["size"],
                "density": cluster["density"]
            }
            explanation["risk_boost"] = 0.1
        
        return explanation
    
    def explain_final_risk(self, 
                          base_risk: float,
                          propagated_risk: float,
                          age_days: float,
                          decayed_risk: float,
                          cluster_boost: float) -> Dict[str, Any]:
        """
        Explain final risk calculation.
        
        Args:
            base_risk: Initial risk
            propagated_risk: After propagation
            age_days: Days since first seen
            decayed_risk: After time decay
            cluster_boost: Clustering impact
            
        Returns:
            Final explanation
        """
        return {
            "calculation_breakdown": {
                "base_risk": round(base_risk, 3),
                "after_propagation": round(propagated_risk, 3),
                "after_time_decay": round(decayed_risk, 3),
                "age_days": round(age_days, 1),
                "cluster_boost": round(cluster_boost, 3)
            },
            "final_risk": round(min(decayed_risk + cluster_boost, 1.0), 3),
            "risk_category": self._categorize_risk(min(decayed_risk + cluster_boost, 1.0)),
            "recommendation": self._get_recommendation(min(decayed_risk + cluster_boost, 1.0))
        }
    
    def _categorize_risk(self, risk: float) -> str:
        """Categorize risk level."""
        if risk < 0.3:
            return "low"
        elif risk < 0.6:
            return "medium"
        else:
            return "high"
    
    def _get_recommendation(self, risk: float) -> str:
        """Get action recommendation."""
        if risk < 0.3:
            return "approve"
        elif risk < 0.6:
            return "review"
        else:
            return "challenge"
