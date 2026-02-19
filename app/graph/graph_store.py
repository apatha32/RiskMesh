"""
Graph Store - NetworkX based in-memory graph for entity relationships
"""
import networkx as nx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GraphStore:
    """
    Manages a directed graph of entities (users, devices, IPs, cards, merchants).
    
    Nodes: user, device, ip, card, merchant
    Edges: relationships with weights
    """
    
    def __init__(self):
        """Initialize the in-memory graph."""
        self.graph = nx.DiGraph()
    
    def add_node(self, node_id: str, node_type: str, risk_score: float = 0.0):
        """
        Add or update a node in the graph.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (user, device, ip, card, merchant)
            risk_score: Initial risk score for the node
        """
        if self.graph.has_node(node_id):
            # Update risk score if node exists
            self.graph.nodes[node_id]['risk_score'] = risk_score
        else:
            # Add new node with attributes
            self.graph.add_node(
                node_id,
                node_type=node_type,
                risk_score=risk_score,
                last_seen=datetime.utcnow()
            )
        logger.debug(f"Added/updated node {node_id} of type {node_type} with risk {risk_score}")
    
    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0):
        """
        Add or update an edge between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            weight: Edge weight for propagation
        """
        # Ensure both nodes exist
        if not self.graph.has_node(source_id):
            self.add_node(source_id, "unknown", 0.0)
        if not self.graph.has_node(target_id):
            self.add_node(target_id, "unknown", 0.0)
        
        # Add or update edge
        if self.graph.has_edge(source_id, target_id):
            # Increment interaction count
            self.graph[source_id][target_id]['interaction_count'] += 1
        else:
            self.graph.add_edge(
                source_id,
                target_id,
                weight=weight,
                interaction_count=1
            )
        logger.debug(f"Added/updated edge {source_id} -> {target_id} with weight {weight}")
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node attributes."""
        if self.graph.has_node(node_id):
            return dict(self.graph.nodes[node_id])
        return None
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """
        Get neighbors within specified depth using BFS.
        
        Args:
            node_id: Starting node
            depth: Maximum number of hops
            
        Returns:
            List of neighbor node IDs
        """
        neighbors = []
        if not self.graph.has_node(node_id):
            return neighbors
        
        visited = {node_id}
        current_level = [node_id]
        
        for _ in range(depth):
            next_level = []
            for node in current_level:
                # Get successors (outgoing edges)
                for neighbor in self.graph.successors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
                        neighbors.append(neighbor)
            current_level = next_level
        
        return neighbors
    
    def update_node_risk(self, node_id: str, risk_score: float):
        """Update risk score for a node."""
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id]['risk_score'] = risk_score
            logger.debug(f"Updated node {node_id} risk to {risk_score}")
        else:
            logger.warning(f"Node {node_id} not found")
    
    def node_count(self) -> int:
        """Get total number of nodes."""
        return self.graph.number_of_nodes()
    
    def edge_count(self) -> int:
        """Get total number of edges."""
        return self.graph.number_of_edges()
