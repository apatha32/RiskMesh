"""
Fraud Ring/Clustering Detection
Identifies coordinated fraud networks using graph algorithms
"""
import logging
from typing import List, Set, Dict, Tuple
import networkx as nx

logger = logging.getLogger(__name__)


class ClusteringDetector:
    """
    Detects fraud rings and clusters.
    
    Uses graph analysis to find:
    - Strongly connected components (circular relationships)
    - Dense subgraphs (many connections)
    - Star patterns (one central node)
    """
    
    def __init__(self, min_cluster_size: int = 3, min_avg_risk: float = 0.6):
        """
        Initialize clustering detector.
        
        Args:
            min_cluster_size: Minimum nodes for a cluster
            min_avg_risk: Minimum average risk to flag
        """
        self.min_cluster_size = min_cluster_size
        self.min_avg_risk = min_avg_risk
    
    def detect_rings(self, graph) -> List[Dict]:
        """
        Detect fraud rings using strongly connected components.
        
        Args:
            graph: GraphStore instance
            
        Returns:
            List of detected rings with stats
        """
        rings = []
        
        # Find strongly connected components (cycles)
        components = nx.strongly_connected_components(graph.graph)
        
        for component in components:
            if len(component) < self.min_cluster_size:
                continue
            
            # Calculate stats for this component
            risks = [graph.get_node(n)['risk_score'] for n in component 
                    if graph.get_node(n)]
            
            avg_risk = sum(risks) / len(risks) if risks else 0.0
            max_risk = max(risks) if risks else 0.0
            
            if avg_risk >= self.min_avg_risk:
                ring = {
                    "type": "ring",
                    "nodes": list(component),
                    "size": len(component),
                    "avg_risk": round(avg_risk, 3),
                    "max_risk": round(max_risk, 3),
                    "risk_sum": round(sum(risks), 3)
                }
                rings.append(ring)
                logger.warning(f"Fraud ring detected: {len(component)} nodes, avg_risk={avg_risk:.3f}")
        
        return rings
    
    def detect_dense_subgraphs(self, graph, density_threshold: float = 0.5) -> List[Dict]:
        """
        Detect dense subgraphs (cliques or near-cliques).
        
        Args:
            graph: GraphStore instance
            density_threshold: Edge density threshold (0-1)
            
        Returns:
            List of dense subgraphs
        """
        clusters = []
        
        # Use k-clique communities
        try:
            for clique in nx.find_cliques(graph.graph.to_undirected()):
                if len(clique) < self.min_cluster_size:
                    continue
                
                # Calculate density
                subgraph = graph.graph.subgraph(clique)
                possible_edges = len(clique) * (len(clique) - 1)
                actual_edges = subgraph.number_of_edges()
                density = actual_edges / possible_edges if possible_edges > 0 else 0
                
                if density >= density_threshold:
                    risks = [graph.get_node(n)['risk_score'] for n in clique 
                            if graph.get_node(n)]
                    avg_risk = sum(risks) / len(risks) if risks else 0.0
                    
                    if avg_risk >= self.min_avg_risk:
                        cluster = {
                            "type": "dense_cluster",
                            "nodes": clique,
                            "size": len(clique),
                            "density": round(density, 3),
                            "avg_risk": round(avg_risk, 3)
                        }
                        clusters.append(cluster)
        except Exception as e:
            logger.debug(f"Dense subgraph detection: {e}")
        
        return clusters
    
    def detect_star_patterns(self, graph, min_degree: int = 5) -> List[Dict]:
        """
        Detect star patterns (one central risky node).
        
        Args:
            graph: GraphStore instance
            min_degree: Minimum edges for central node
            
        Returns:
            List of detected stars
        """
        stars = []
        
        for node_id, degree in graph.graph.out_degree():
            if degree < min_degree:
                continue
            
            node = graph.get_node(node_id)
            if not node or node['risk_score'] < self.min_avg_risk:
                continue
            
            # Get neighbors
            neighbors = list(graph.graph.successors(node_id))
            neighbor_risks = [graph.get_node(n)['risk_score'] for n in neighbors 
                            if graph.get_node(n)]
            
            avg_neighbor_risk = sum(neighbor_risks) / len(neighbor_risks) if neighbor_risks else 0
            
            star = {
                "type": "star",
                "center": node_id,
                "center_risk": round(node['risk_score'], 3),
                "branches": len(neighbors),
                "avg_neighbor_risk": round(avg_neighbor_risk, 3)
            }
            stars.append(star)
            logger.warning(f"Star pattern: {node_id} with {len(neighbors)} connections")
        
        return stars
    
    def detect_all_clusters(self, graph) -> Dict:
        """
        Run all clustering detection algorithms.
        
        Args:
            graph: GraphStore instance
            
        Returns:
            Dictionary with all detected clusters
        """
        return {
            "rings": self.detect_rings(graph),
            "dense_clusters": self.detect_dense_subgraphs(graph),
            "stars": self.detect_star_patterns(graph)
        }
    
    def boost_cluster_risk(self, graph, cluster: Dict, boost_factor: float = 0.2) -> int:
        """
        Increase risk for all nodes in a detected cluster.
        
        Args:
            graph: GraphStore instance
            cluster: Cluster dict from detection
            boost_factor: Risk increase amount
            
        Returns:
            Number of nodes updated
        """
        nodes = cluster.get('nodes') or [cluster.get('center')]
        if not nodes:
            return 0
        
        updated = 0
        for node_id in nodes:
            node = graph.get_node(node_id)
            if node:
                old_risk = node['risk_score']
                new_risk = min(1.0, old_risk + boost_factor)
                graph.update_node_risk(node_id, new_risk)
                updated += 1
        
        logger.info(f"Boosted risk for {updated} nodes in cluster")
        return updated
