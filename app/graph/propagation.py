"""
Risk Propagation Algorithm
"""
from typing import Dict, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskPropagator:
    """
    Implements risk propagation algorithm across graph.
    
    Formula:
    NewRisk(node) = BaseRisk + alpha × sum(neighborRisk × edgeWeight)
    
    - alpha: propagation coefficient (0.5)
    - depth: propagation depth (2 hops)
    """
    
    def __init__(self, alpha: float = 0.5, max_depth: int = 2, risk_threshold: float = 0.1):
        """
        Initialize propagator.
        
        Args:
            alpha: Propagation coefficient
            max_depth: Maximum propagation depth
            risk_threshold: Minimum risk to trigger propagation
        """
        self.alpha = alpha
        self.max_depth = max_depth
        self.risk_threshold = risk_threshold
    
    def propagate(self, graph, source_node_id: str, base_risk: float) -> Dict[str, float]:
        """
        Propagate risk from source node through graph.
        
        Formula:
        NewRisk(node) = BaseRisk + alpha × sum(neighborRisk × edgeWeight)
        
        Args:
            graph: GraphStore instance
            source_node_id: Starting node ID
            base_risk: Base risk score for source node
            
        Returns:
            Dictionary of node_id -> new_risk_score
        """
        if base_risk < self.risk_threshold:
            # Skip propagation if risk is below threshold
            logger.debug(f"Risk {base_risk} below threshold {self.risk_threshold}, skipping propagation")
            return {source_node_id: base_risk}
        
        # Initialize risk propagation
        risk_scores = {source_node_id: base_risk}
        visited = {source_node_id}
        
        # BFS propagation with depth limit
        current_level = [(source_node_id, base_risk)]
        current_depth = 0
        
        while current_level and current_depth < self.max_depth:
            next_level = []
            
            for node_id, current_risk in current_level:
                # Get neighbors from graph
                if not hasattr(graph.graph, 'successors'):
                    logger.warning("Graph doesn't have successors method")
                    continue
                
                # Propagate to neighbors
                for neighbor_id in graph.graph.successors(node_id):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        
                        # Get edge weight
                        edge_data = graph.graph[node_id][neighbor_id]
                        edge_weight = edge_data.get('weight', 1.0)
                        
                        # Get neighbor's current risk
                        neighbor_node = graph.get_node(neighbor_id)
                        neighbor_base_risk = neighbor_node['risk_score'] if neighbor_node else 0.0
                        
                        # Calculate new risk using propagation formula
                        propagated_component = self.alpha * (current_risk * edge_weight)
                        new_risk = min(neighbor_base_risk + propagated_component, 1.0)  # Cap at 1.0
                        
                        risk_scores[neighbor_id] = new_risk
                        next_level.append((neighbor_id, new_risk))
                        
                        logger.debug(
                            f"Propagated risk to {neighbor_id}: "
                            f"base={neighbor_base_risk:.3f} + {propagated_component:.3f} = {new_risk:.3f}"
                        )
            
            current_level = next_level
            current_depth += 1
        
        logger.info(f"Risk propagation complete: {len(risk_scores)} nodes affected, depth={current_depth}")
        return risk_scores
