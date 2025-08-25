"""
Enterprise Vector Store for Design Pattern Storage and Retrieval
==============================================================

Advanced vector database system for storing and retrieving similar electrical
designs to enable AI-powered wiring suggestions based on historical patterns.
This module provides semantic search capabilities over design graphs, enabling
retrieval-augmented generation (RAG) for intelligent wiring recommendations.

Key Features:
- Design pattern vectorization using graph embeddings
- Similarity search for component layouts and topologies
- Metadata filtering by system type, power rating, and compliance codes
- Batch operations for efficient design storage and retrieval
- Integration with enterprise monitoring and audit systems
"""

from __future__ import annotations

import logging
import hashlib
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class DesignCategory(Enum):
    """Design pattern categories for classification."""
    RESIDENTIAL_PV = "residential_pv"
    COMMERCIAL_PV = "commercial_pv"
    BATTERY_STORAGE = "battery_storage"
    HYBRID_SYSTEM = "hybrid_system"
    MICROINVERTER = "microinverter"
    STRING_INVERTER = "string_inverter"
    POWER_OPTIMIZER = "power_optimizer"


@dataclass
class DesignMetadata:
    """Comprehensive metadata for design patterns."""
    system_type: str
    power_rating: float  # kW
    voltage_class: str  # "LV", "MV", "HV"
    component_count: int
    connection_count: int
    compliance_codes: List[str]  # ["NEC_2020", "UL_1741", etc.]
    geographical_region: str
    installation_type: str  # "rooftop", "ground_mount", "carport", etc.
    design_category: DesignCategory
    performance_metrics: Dict[str, float]
    creation_timestamp: float
    designer_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class DesignPattern:
    """Complete design pattern with graph data and metadata."""
    pattern_id: str
    graph_data: Dict[str, Any]  # Serialized ODL graph
    metadata: DesignMetadata
    embedding: Optional[List[float]] = None
    similarity_hash: Optional[str] = None


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    pattern: DesignPattern
    similarity_score: float
    match_factors: Dict[str, float]  # Breakdown of similarity components


class GraphEmbeddingEngine:
    """
    Advanced graph embedding system for converting ODL designs into vectors.
    Uses multiple feature extraction techniques to capture structural and
    electrical characteristics of designs.
    """
    
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self.feature_extractors = self._init_feature_extractors()
    
    def _init_feature_extractors(self) -> Dict[str, Any]:
        """Initialize feature extraction functions."""
        return {
            "topology": self._extract_topology_features,
            "component_distribution": self._extract_component_features,
            "electrical_properties": self._extract_electrical_features,
            "spatial_layout": self._extract_spatial_features,
            "connection_patterns": self._extract_connection_features
        }
    
    def generate_embedding(self, graph_data: Dict[str, Any]) -> List[float]:
        """
        Generate a comprehensive embedding vector for an ODL graph.
        
        Args:
            graph_data: Serialized ODL graph with nodes and edges
            
        Returns:
            Dense embedding vector representing the design pattern
        """
        feature_vectors = []
        
        # Extract features using different techniques
        for extractor_name, extractor_func in self.feature_extractors.items():
            try:
                features = extractor_func(graph_data)
                feature_vectors.append(features)
            except Exception as e:
                logger.warning(f"Failed to extract {extractor_name} features: {e}")
                # Add zero vector as fallback
                feature_vectors.append(np.zeros(self.embedding_dim // len(self.feature_extractors)))
        
        # Concatenate and normalize
        combined_features = np.concatenate(feature_vectors)
        
        # Pad or truncate to target dimension
        if len(combined_features) > self.embedding_dim:
            embedding = combined_features[:self.embedding_dim]
        else:
            embedding = np.pad(combined_features, (0, self.embedding_dim - len(combined_features)))
        
        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.tolist()
    
    def _extract_topology_features(self, graph_data: Dict[str, Any]) -> np.ndarray:
        """Extract graph topology features (connectivity patterns)."""
        nodes = graph_data.get("nodes", {})
        edges = graph_data.get("edges", [])
        
        if not nodes:
            return np.zeros(64)
        
        # Basic topology metrics
        node_count = len(nodes)
        edge_count = len(edges)
        density = edge_count / max(node_count * (node_count - 1) / 2, 1)
        
        # Degree distribution
        degree_counts = {}
        for edge in edges:
            source = edge.get("source", edge.get("source_id"))
            target = edge.get("target", edge.get("target_id"))
            degree_counts[source] = degree_counts.get(source, 0) + 1
            degree_counts[target] = degree_counts.get(target, 0) + 1
        
        degrees = list(degree_counts.values())
        avg_degree = np.mean(degrees) if degrees else 0
        max_degree = np.max(degrees) if degrees else 0
        degree_variance = np.var(degrees) if degrees else 0
        
        # Component type distribution
        type_counts = {}
        for node in nodes.values():
            node_type = node.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        # Create feature vector
        features = [
            node_count / 100.0,  # Normalized node count
            edge_count / 100.0,  # Normalized edge count
            density,
            avg_degree / 10.0,   # Normalized average degree
            max_degree / 20.0,   # Normalized max degree
            degree_variance / 100.0,
            len(type_counts) / 10.0  # Type diversity
        ]
        
        # Pad to target size
        return np.pad(np.array(features), (0, 64 - len(features)))
    
    def _extract_component_features(self, graph_data: Dict[str, Any]) -> np.ndarray:
        """Extract component type and distribution features."""
        nodes = graph_data.get("nodes", {})
        
        if not nodes:
            return np.zeros(128)
        
        # Component type frequencies
        component_types = ["panel", "inverter", "battery", "protection", "disconnect", 
                         "monitoring", "combiner", "optimizer", "meter", "transformer"]
        type_features = []
        
        total_nodes = len(nodes)
        for comp_type in component_types:
            count = sum(1 for node in nodes.values() 
                       if comp_type in node.get("type", "").lower())
            type_features.append(count / max(total_nodes, 1))
        
        # Power and electrical characteristics
        total_power = 0
        voltage_levels = []
        current_levels = []
        
        for node in nodes.values():
            attrs = node.get("attrs", {}) or node.get("data", {})
            power = attrs.get("power", 0)
            voltage = attrs.get("voltage", attrs.get("voltage_oc", attrs.get("voc", 0)))
            current = attrs.get("current", attrs.get("current_sc", attrs.get("isc", 0)))
            
            if power > 0:
                total_power += power
            if voltage > 0:
                voltage_levels.append(voltage)
            if current > 0:
                current_levels.append(current)
        
        electrical_features = [
            total_power / 10000.0,  # Normalized total power (10kW scale)
            np.mean(voltage_levels) / 1000.0 if voltage_levels else 0,  # Avg voltage
            np.std(voltage_levels) / 100.0 if voltage_levels else 0,    # Voltage spread
            np.mean(current_levels) / 50.0 if current_levels else 0,    # Avg current
            np.std(current_levels) / 10.0 if current_levels else 0      # Current spread
        ]
        
        features = type_features + electrical_features
        return np.pad(np.array(features), (0, 128 - len(features)))
    
    def _extract_electrical_features(self, graph_data: Dict[str, Any]) -> np.ndarray:
        """Extract electrical system characteristics."""
        nodes = graph_data.get("nodes", {})
        edges = graph_data.get("edges", [])
        
        if not nodes:
            return np.zeros(96)
        
        # Electrical topology patterns
        dc_connections = sum(1 for edge in edges if "dc" in edge.get("kind", "").lower())
        ac_connections = sum(1 for edge in edges if "ac" in edge.get("kind", "").lower())
        total_connections = max(len(edges), 1)
        
        # System voltage classification
        voltage_levels = {"lv": 0, "mv": 0, "hv": 0}  # Low/Medium/High voltage counts
        for node in nodes.values():
            attrs = node.get("attrs", {}) or node.get("data", {})
            voltage = attrs.get("voltage", attrs.get("voltage_oc", 0))
            
            if voltage < 50:
                voltage_levels["lv"] += 1
            elif voltage < 1000:
                voltage_levels["mv"] += 1
            else:
                voltage_levels["hv"] += 1
        
        # String/parallel analysis for PV systems
        panel_nodes = [nid for nid, node in nodes.items() 
                      if "panel" in node.get("type", "").lower()]
        string_count = 0
        parallel_count = 0
        
        # Simple heuristic: count series vs parallel connections
        for edge in edges:
            if edge.get("kind") == "electrical":
                source_id = edge.get("source", edge.get("source_id"))
                target_id = edge.get("target", edge.get("target_id"))
                
                if source_id in panel_nodes and target_id in panel_nodes:
                    # Panel-to-panel connection suggests string topology
                    string_count += 1
                elif (source_id in panel_nodes or target_id in panel_nodes):
                    # Panel-to-inverter suggests parallel branch
                    parallel_count += 1
        
        features = [
            dc_connections / total_connections,
            ac_connections / total_connections,
            voltage_levels["lv"] / max(len(nodes), 1),
            voltage_levels["mv"] / max(len(nodes), 1),
            voltage_levels["hv"] / max(len(nodes), 1),
            string_count / max(len(panel_nodes), 1),
            parallel_count / max(len(panel_nodes), 1)
        ]
        
        return np.pad(np.array(features), (0, 96 - len(features)))
    
    def _extract_spatial_features(self, graph_data: Dict[str, Any]) -> np.ndarray:
        """Extract spatial layout and positioning features."""
        nodes = graph_data.get("nodes", {})
        
        if not nodes:
            return np.zeros(64)
        
        # Extract spatial coordinates
        positions = []
        for node in nodes.values():
            attrs = node.get("attrs", {}) or node.get("data", {})
            x = attrs.get("x", 0)
            y = attrs.get("y", 0)
            if x != 0 or y != 0:  # Only include positioned nodes
                positions.append((x, y))
        
        if not positions:
            return np.zeros(64)
        
        positions = np.array(positions)
        
        # Spatial distribution metrics
        centroid = np.mean(positions, axis=0)
        distances_from_center = np.linalg.norm(positions - centroid, axis=1)
        
        # Bounding box analysis
        x_min, y_min = np.min(positions, axis=0)
        x_max, y_max = np.max(positions, axis=0)
        width = x_max - x_min
        height = y_max - y_min
        aspect_ratio = width / max(height, 0.1)
        
        # Spatial clustering analysis
        pairwise_distances = []
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                dist = np.linalg.norm(pos1 - pos2)
                pairwise_distances.append(dist)
        
        features = [
            width / 1000.0,  # Normalized width (assume meter scale)
            height / 1000.0,  # Normalized height
            aspect_ratio / 10.0,  # Normalized aspect ratio
            np.mean(distances_from_center) / 100.0,  # Avg distance from center
            np.std(distances_from_center) / 100.0,   # Spatial spread
            np.mean(pairwise_distances) / 100.0 if pairwise_distances else 0,  # Avg spacing
            np.std(pairwise_distances) / 100.0 if pairwise_distances else 0    # Spacing variance
        ]
        
        return np.pad(np.array(features), (0, 64 - len(features)))
    
    def _extract_connection_features(self, graph_data: Dict[str, Any]) -> np.ndarray:
        """Extract connection pattern features."""
        edges = graph_data.get("edges", [])
        
        if not edges:
            return np.zeros(96)
        
        # Connection type analysis
        connection_types = {}
        for edge in edges:
            conn_type = edge.get("kind", "unknown")
            connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
        
        # Port-level connection analysis
        port_usage = {"input": 0, "output": 0, "bidirectional": 0}
        for edge in edges:
            source_port = edge.get("source_port", "")
            target_port = edge.get("target_port", "")
            
            # Simple heuristics based on port names
            if "out" in source_port.lower() or "pos" in source_port.lower():
                port_usage["output"] += 1
            elif "in" in target_port.lower() or "neg" in target_port.lower():
                port_usage["input"] += 1
            else:
                port_usage["bidirectional"] += 1
        
        total_edges = len(edges)
        features = [
            connection_types.get("electrical", 0) / total_edges,
            connection_types.get("dc", 0) / total_edges,
            connection_types.get("ac", 0) / total_edges,
            port_usage["output"] / total_edges,
            port_usage["input"] / total_edges,
            port_usage["bidirectional"] / total_edges
        ]
        
        return np.pad(np.array(features), (0, 96 - len(features)))


class EnterpriseVectorStore:
    """
    Enterprise-grade vector database for design pattern storage and retrieval.
    Provides semantic search capabilities with metadata filtering and
    performance optimization for large-scale design repositories.
    """
    
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or "vector_store.json"
        self.embedding_engine = GraphEmbeddingEngine()
        self.patterns: Dict[str, DesignPattern] = {}
        self.index_dirty = True
        self._load_store()
    
    def _load_store(self):
        """Load existing patterns from persistent storage."""
        try:
            import os
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    
                for pattern_data in data.get("patterns", []):
                    metadata_dict = pattern_data["metadata"]
                    metadata_dict["design_category"] = DesignCategory(metadata_dict["design_category"])
                    
                    pattern = DesignPattern(
                        pattern_id=pattern_data["pattern_id"],
                        graph_data=pattern_data["graph_data"],
                        metadata=DesignMetadata(**metadata_dict),
                        embedding=pattern_data.get("embedding"),
                        similarity_hash=pattern_data.get("similarity_hash")
                    )
                    self.patterns[pattern.pattern_id] = pattern
                    
                logger.info(f"Loaded {len(self.patterns)} design patterns from {self.store_path}")
        except Exception as e:
            logger.warning(f"Failed to load vector store: {e}")
    
    def _save_store(self):
        """Persist patterns to storage."""
        try:
            patterns_data = []
            for pattern in self.patterns.values():
                metadata_dict = asdict(pattern.metadata)
                metadata_dict["design_category"] = pattern.metadata.design_category.value
                
                patterns_data.append({
                    "pattern_id": pattern.pattern_id,
                    "graph_data": pattern.graph_data,
                    "metadata": metadata_dict,
                    "embedding": pattern.embedding,
                    "similarity_hash": pattern.similarity_hash
                })
            
            data = {
                "version": "1.0",
                "patterns": patterns_data,
                "total_patterns": len(patterns_data)
            }
            
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.patterns)} design patterns to {self.store_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def _generate_similarity_hash(self, graph_data: Dict[str, Any]) -> str:
        """Generate hash for duplicate detection."""
        # Create normalized representation for hashing
        nodes = graph_data.get("nodes", {})
        edges = graph_data.get("edges", [])
        
        # Sort nodes and edges for consistent hashing
        sorted_nodes = sorted([(nid, node.get("type")) for nid, node in nodes.items()])
        sorted_edges = sorted([(e.get("source"), e.get("target"), e.get("kind")) for e in edges])
        
        hash_content = json.dumps({"nodes": sorted_nodes, "edges": sorted_edges}, sort_keys=True)
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def store_design(self, graph_data: Dict[str, Any], metadata: DesignMetadata) -> str:
        """
        Store a new design pattern in the vector database.
        
        Args:
            graph_data: Serialized ODL graph
            metadata: Design metadata for filtering and classification
            
        Returns:
            Pattern ID of the stored design
        """
        # Generate unique pattern ID
        similarity_hash = self._generate_similarity_hash(graph_data)
        pattern_id = f"pattern_{similarity_hash[:8]}_{int(metadata.creation_timestamp)}"
        
        # Check for duplicates
        existing_pattern = next(
            (p for p in self.patterns.values() if p.similarity_hash == similarity_hash),
            None
        )
        
        if existing_pattern:
            logger.info(f"Similar pattern already exists: {existing_pattern.pattern_id}")
            return existing_pattern.pattern_id
        
        # Generate embedding
        try:
            embedding = self.embedding_engine.generate_embedding(graph_data)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            embedding = [0.0] * 512  # Fallback zero vector
        
        # Create and store pattern
        pattern = DesignPattern(
            pattern_id=pattern_id,
            graph_data=graph_data,
            metadata=metadata,
            embedding=embedding,
            similarity_hash=similarity_hash
        )
        
        self.patterns[pattern_id] = pattern
        self.index_dirty = True
        self._save_store()
        
        logger.info(f"Stored design pattern {pattern_id} with {len(graph_data.get('nodes', {}))} nodes")
        return pattern_id
    
    def search_similar(
        self,
        query_graph: Dict[str, Any],
        top_k: int = 5,
        min_similarity: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar design patterns using vector similarity.
        
        Args:
            query_graph: ODL graph to find similar designs for
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            filters: Optional metadata filters
            
        Returns:
            List of similar design patterns ranked by similarity
        """
        if not self.patterns:
            logger.warning("No patterns stored in vector database")
            return []
        
        # Generate query embedding
        try:
            query_embedding = np.array(self.embedding_engine.generate_embedding(query_graph))
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []
        
        results = []
        
        for pattern in self.patterns.values():
            # Apply metadata filters
            if filters and not self._matches_filters(pattern.metadata, filters):
                continue
            
            if not pattern.embedding:
                continue
            
            # Calculate cosine similarity
            pattern_embedding = np.array(pattern.embedding)
            similarity = np.dot(query_embedding, pattern_embedding)
            
            if similarity >= min_similarity:
                # Calculate detailed match factors
                match_factors = self._calculate_match_factors(query_graph, pattern.graph_data)
                
                results.append(SearchResult(
                    pattern=pattern,
                    similarity_score=similarity,
                    match_factors=match_factors
                ))
        
        # Sort by similarity and return top-k
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
    
    def _matches_filters(self, metadata: DesignMetadata, filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria."""
        for filter_key, filter_value in filters.items():
            if filter_key == "power_range":
                min_power, max_power = filter_value
                if not (min_power <= metadata.power_rating <= max_power):
                    return False
            elif filter_key == "system_type":
                if metadata.system_type != filter_value:
                    return False
            elif filter_key == "design_category":
                if metadata.design_category != filter_value:
                    return False
            elif filter_key == "compliance_codes":
                if not any(code in metadata.compliance_codes for code in filter_value):
                    return False
        
        return True
    
    def _calculate_match_factors(self, query_graph: Dict[str, Any], pattern_graph: Dict[str, Any]) -> Dict[str, float]:
        """Calculate detailed similarity breakdown."""
        factors = {}
        
        # Component type similarity
        query_types = set()
        pattern_types = set()
        
        for node in query_graph.get("nodes", {}).values():
            query_types.add(node.get("type", "unknown"))
        
        for node in pattern_graph.get("nodes", {}).values():
            pattern_types.add(node.get("type", "unknown"))
        
        if query_types and pattern_types:
            type_overlap = len(query_types & pattern_types)
            type_union = len(query_types | pattern_types)
            factors["component_types"] = type_overlap / type_union
        else:
            factors["component_types"] = 0.0
        
        # Scale similarity
        query_node_count = len(query_graph.get("nodes", {}))
        pattern_node_count = len(pattern_graph.get("nodes", {}))
        
        if query_node_count > 0 and pattern_node_count > 0:
            scale_ratio = min(query_node_count, pattern_node_count) / max(query_node_count, pattern_node_count)
            factors["scale_similarity"] = scale_ratio
        else:
            factors["scale_similarity"] = 0.0
        
        # Connection pattern similarity  
        query_edge_count = len(query_graph.get("edges", []))
        pattern_edge_count = len(pattern_graph.get("edges", []))
        
        if query_edge_count > 0 and pattern_edge_count > 0:
            edge_ratio = min(query_edge_count, pattern_edge_count) / max(query_edge_count, pattern_edge_count)
            factors["connection_patterns"] = edge_ratio
        else:
            factors["connection_patterns"] = 0.0
        
        return factors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self.patterns:
            return {"total_patterns": 0}
        
        category_counts = {}
        power_ratings = []
        
        for pattern in self.patterns.values():
            category = pattern.metadata.design_category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            power_ratings.append(pattern.metadata.power_rating)
        
        return {
            "total_patterns": len(self.patterns),
            "categories": category_counts,
            "power_range": {
                "min": min(power_ratings) if power_ratings else 0,
                "max": max(power_ratings) if power_ratings else 0,
                "avg": np.mean(power_ratings) if power_ratings else 0
            },
            "embedding_dimension": self.embedding_engine.embedding_dim
        }


# Convenience functions for backward compatibility and simple usage
def retrieve_similar(
    query_graph: Dict[str, Any],
    top_n: int = 3,
    store_path: Optional[str] = None
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Simplified similar design retrieval function for backward compatibility.
    
    Args:
        query_graph: ODL graph to find similar designs for
        top_n: Number of similar designs to retrieve
        store_path: Optional path to vector store file
        
    Returns:
        List of (graph_data, metadata) tuples for similar designs
    """
    store = EnterpriseVectorStore(store_path)
    results = store.search_similar(query_graph, top_k=top_n, min_similarity=0.1)
    
    return [(result.pattern.graph_data, asdict(result.pattern.metadata)) for result in results]


def store_design_pattern(
    graph_data: Dict[str, Any],
    system_type: str,
    power_rating: float,
    additional_metadata: Optional[Dict[str, Any]] = None,
    store_path: Optional[str] = None
) -> str:
    """
    Simplified design pattern storage function.
    
    Args:
        graph_data: Serialized ODL graph
        system_type: Type of electrical system
        power_rating: System power rating in kW
        additional_metadata: Optional additional metadata
        store_path: Optional path to vector store file
        
    Returns:
        Pattern ID of stored design
    """
    import time
    
    additional_metadata = additional_metadata or {}
    
    metadata = DesignMetadata(
        system_type=system_type,
        power_rating=power_rating,
        voltage_class=additional_metadata.get("voltage_class", "LV"),
        component_count=len(graph_data.get("nodes", {})),
        connection_count=len(graph_data.get("edges", [])),
        compliance_codes=additional_metadata.get("compliance_codes", ["NEC_2020"]),
        geographical_region=additional_metadata.get("geographical_region", "US"),
        installation_type=additional_metadata.get("installation_type", "rooftop"),
        design_category=DesignCategory(additional_metadata.get("design_category", "residential_pv")),
        performance_metrics=additional_metadata.get("performance_metrics", {}),
        creation_timestamp=time.time(),
        designer_id=additional_metadata.get("designer_id"),
        project_id=additional_metadata.get("project_id")
    )
    
    store = EnterpriseVectorStore(store_path)
    return store.store_design(graph_data, metadata)