"""
Network Analysis System for ArXiv MCP

This module provides comprehensive network analysis capabilities including
citation networks, author collaboration networks, and topic relationship analysis.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .logging import structured_logger
from .optional_deps import safe_import


logger = structured_logger()

# Safe import for networkx
try:
    networkx = safe_import("networkx")
    NETWORKX_AVAILABLE = networkx is not None
except Exception:
    networkx = None
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available. Network analysis will be limited.")


class NetworkType(Enum):
    """Types of networks that can be analyzed."""

    CITATION = "citation"
    COLLABORATION = "collaboration"
    TOPIC = "topic"
    KEYWORD = "keyword"
    AUTHOR = "author"


@dataclass
class NetworkNode:
    """Represents a node in a network."""

    node_id: str
    node_type: str
    label: str
    attributes: Dict[str, Any] = None
    centrality_scores: Dict[str, float] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.centrality_scores is None:
            self.centrality_scores = {}


@dataclass
class NetworkEdge:
    """Represents an edge in a network."""

    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "default"
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class NetworkMetrics:
    """Comprehensive network metrics."""

    total_nodes: int
    total_edges: int
    density: float
    clustering_coefficient: float
    average_path_length: float
    diameter: int
    connected_components: int
    largest_component_size: int
    small_world_coefficient: float = None
    scale_free_exponent: float = None


@dataclass
class NetworkAnalysisResult:
    """Complete network analysis result."""

    network_type: NetworkType
    metrics: NetworkMetrics
    top_nodes: List[Dict[str, Any]]
    communities: List[List[str]] = None
    central_nodes: Dict[str, List[str]] = None
    analysis_timestamp: datetime = None

    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()


class NetworkAnalyzer:
    """
    Comprehensive network analysis system.

    Features:
    - Citation network analysis
    - Author collaboration networks
    - Topic relationship networks
    - Centrality analysis (degree, betweenness, closeness, PageRank)
    - Community detection
    - Path analysis
    - Network visualization data preparation
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the network analyzer."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "network_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "networks.db"
        self._init_database()

        if not NETWORKX_AVAILABLE:
            logger.warning(
                "NetworkX not available. Some advanced network analysis features will be disabled."
            )

        logger.info(f"NetworkAnalyzer initialized with cache: {self.cache_dir}")

    def _init_database(self) -> None:
        """Initialize SQLite database for network data."""
        with sqlite3.connect(self.db_path) as conn:
            # Networks table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS networks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network_type TEXT NOT NULL,
                    network_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # Nodes table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS network_nodes (
                    network_id INTEGER,
                    node_id TEXT,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    attributes TEXT,
                    centrality_scores TEXT,
                    PRIMARY KEY (network_id, node_id),
                    FOREIGN KEY (network_id) REFERENCES networks (id)
                )
            """
            )

            # Edges table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS network_edges (
                    network_id INTEGER,
                    source TEXT,
                    target TEXT,
                    weight REAL DEFAULT 1.0,
                    edge_type TEXT DEFAULT 'default',
                    attributes TEXT,
                    PRIMARY KEY (network_id, source, target),
                    FOREIGN KEY (network_id) REFERENCES networks (id)
                )
            """
            )

            # Analysis results table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS network_analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network_id INTEGER,
                    analysis_type TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (network_id) REFERENCES networks (id)
                )
            """
            )

            conn.commit()

    def create_citation_network(self, papers: List[Dict[str, Any]]) -> int:
        """Create a citation network from paper data."""
        logger.info(f"Creating citation network from {len(papers)} papers")

        try:
            # Create network record
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO networks (network_type, network_name, metadata)
                    VALUES (?, ?, ?)
                """,
                    (
                        NetworkType.CITATION.value,
                        f"citation_network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        json.dumps(
                            {"paper_count": len(papers), "created_from": "paper_data"}
                        ),
                    ),
                )
                network_id = cursor.lastrowid

            # Process papers and create nodes/edges
            nodes = {}
            edges = []

            for paper in papers:
                paper_id = paper.get("id", paper.get("arxiv_id", "unknown"))
                title = paper.get("title", "Unknown Title")
                authors = paper.get("authors", [])

                # Create paper node
                nodes[paper_id] = NetworkNode(
                    node_id=paper_id,
                    node_type="paper",
                    label=title,
                    attributes={
                        "authors": authors,
                        "publication_date": paper.get("published", ""),
                        "categories": paper.get("categories", []),
                    },
                )

                # Create citation edges
                citations = paper.get("citations", [])
                for citation in citations:
                    if isinstance(citation, str):
                        citation_id = citation
                    elif isinstance(citation, dict):
                        citation_id = citation.get("id", citation.get("arxiv_id"))
                    else:
                        continue

                    if citation_id:
                        edges.append(
                            NetworkEdge(
                                source=paper_id,
                                target=citation_id,
                                weight=1.0,
                                edge_type="citation",
                                attributes={"relationship": "cites"},
                            )
                        )

                        # Create cited paper node if not exists
                        if citation_id not in nodes:
                            nodes[citation_id] = NetworkNode(
                                node_id=citation_id,
                                node_type="paper",
                                label=(
                                    citation.get("title", citation_id)
                                    if isinstance(citation, dict)
                                    else citation_id
                                ),
                                attributes={"is_external": True},
                            )

            # Store nodes and edges
            self._store_network_data(network_id, nodes, edges)

            logger.info(
                f"Citation network created with ID {network_id}: {len(nodes)} nodes, {len(edges)} edges"
            )
            return network_id

        except Exception as e:
            logger.error(f"Failed to create citation network: {e}")
            return -1

    def create_collaboration_network(self, papers: List[Dict[str, Any]]) -> int:
        """Create an author collaboration network from paper data."""
        logger.info(f"Creating collaboration network from {len(papers)} papers")

        try:
            # Create network record
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO networks (network_type, network_name, metadata)
                    VALUES (?, ?, ?)
                """,
                    (
                        NetworkType.COLLABORATION.value,
                        f"collaboration_network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        json.dumps(
                            {"paper_count": len(papers), "created_from": "paper_data"}
                        ),
                    ),
                )
                network_id = cursor.lastrowid

            # Track author collaborations
            author_papers = {}  # author -> list of papers
            collaboration_counts = {}  # (author1, author2) -> count

            for paper in papers:
                authors = paper.get("authors", [])
                paper_id = paper.get("id", paper.get("arxiv_id", "unknown"))

                # Track which papers each author worked on
                for author in authors:
                    if author not in author_papers:
                        author_papers[author] = []
                    author_papers[author].append(paper_id)

                # Count collaborations
                for i, author1 in enumerate(authors):
                    for author2 in authors[i + 1 :]:
                        # Ensure consistent ordering
                        pair = tuple(sorted([author1, author2]))
                        collaboration_counts[pair] = (
                            collaboration_counts.get(pair, 0) + 1
                        )

            # Create nodes (authors)
            nodes = {}
            for author, papers_list in author_papers.items():
                nodes[author] = NetworkNode(
                    node_id=author,
                    node_type="author",
                    label=author,
                    attributes={"paper_count": len(papers_list), "papers": papers_list},
                )

            # Create edges (collaborations)
            edges = []
            for (author1, author2), count in collaboration_counts.items():
                edges.append(
                    NetworkEdge(
                        source=author1,
                        target=author2,
                        weight=float(count),
                        edge_type="collaboration",
                        attributes={"collaboration_count": count},
                    )
                )

            # Store network data
            self._store_network_data(network_id, nodes, edges)

            logger.info(
                f"Collaboration network created with ID {network_id}: {len(nodes)} authors, {len(edges)} collaborations"
            )
            return network_id

        except Exception as e:
            logger.error(f"Failed to create collaboration network: {e}")
            return -1

    def analyze_network(self, network_id: int) -> NetworkAnalysisResult:
        """Perform comprehensive network analysis."""
        logger.info(f"Analyzing network {network_id}")

        try:
            # Load network data
            nodes, edges, network_type = self._load_network_data(network_id)

            if not NETWORKX_AVAILABLE:
                return self._basic_network_analysis(
                    network_id, nodes, edges, NetworkType(network_type)
                )

            # Create NetworkX graph
            G = networkx.Graph()

            # Add nodes
            for node in nodes.values():
                G.add_node(node.node_id, **node.attributes)

            # Add edges
            for edge in edges:
                G.add_edge(
                    edge.source, edge.target, weight=edge.weight, **edge.attributes
                )

            # Calculate basic metrics
            total_nodes = G.number_of_nodes()
            total_edges = G.number_of_edges()
            density = networkx.density(G)

            # Calculate clustering coefficient
            clustering_coefficient = networkx.average_clustering(G)

            # Calculate path-based metrics for connected graph
            if networkx.is_connected(G):
                average_path_length = networkx.average_shortest_path_length(G)
                diameter = networkx.diameter(G)
                connected_components = 1
                largest_component_size = total_nodes
            else:
                # Use largest connected component
                largest_cc = max(networkx.connected_components(G), key=len)
                largest_subgraph = G.subgraph(largest_cc)

                if len(largest_cc) > 1:
                    average_path_length = networkx.average_shortest_path_length(
                        largest_subgraph
                    )
                    diameter = networkx.diameter(largest_subgraph)
                else:
                    average_path_length = 0
                    diameter = 0

                connected_components = networkx.number_connected_components(G)
                largest_component_size = len(largest_cc)

            # Calculate centrality measures
            degree_centrality = networkx.degree_centrality(G)
            betweenness_centrality = networkx.betweenness_centrality(G)
            closeness_centrality = networkx.closeness_centrality(G)

            # PageRank for directed analysis (treat as directed for PageRank)
            pagerank = networkx.pagerank(G)

            # Find top nodes by different centrality measures
            top_degree = sorted(
                degree_centrality.items(), key=lambda x: x[1], reverse=True
            )[:10]
            top_betweenness = sorted(
                betweenness_centrality.items(), key=lambda x: x[1], reverse=True
            )[:10]
            top_closeness = sorted(
                closeness_centrality.items(), key=lambda x: x[1], reverse=True
            )[:10]
            top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            # Community detection (if possible)
            communities = []
            try:
                if hasattr(networkx, "community") and hasattr(
                    networkx.community, "greedy_modularity_communities"
                ):
                    communities = list(
                        networkx.community.greedy_modularity_communities(G)
                    )
                    communities = [list(community) for community in communities]
            except Exception:
                logger.warning("Community detection failed")

            # Create metrics object
            metrics = NetworkMetrics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                density=density,
                clustering_coefficient=clustering_coefficient,
                average_path_length=average_path_length,
                diameter=diameter,
                connected_components=connected_components,
                largest_component_size=largest_component_size,
            )

            # Prepare top nodes summary
            top_nodes = []
            for node_id, score in top_degree[:5]:
                node_data = nodes.get(node_id)
                top_nodes.append(
                    {
                        "node_id": node_id,
                        "label": node_data.label if node_data else node_id,
                        "degree_centrality": degree_centrality.get(node_id, 0),
                        "betweenness_centrality": betweenness_centrality.get(
                            node_id, 0
                        ),
                        "closeness_centrality": closeness_centrality.get(node_id, 0),
                        "pagerank": pagerank.get(node_id, 0),
                    }
                )

            # Create analysis result
            result = NetworkAnalysisResult(
                network_type=NetworkType(network_type),
                metrics=metrics,
                top_nodes=top_nodes,
                communities=communities,
                central_nodes={
                    "degree": [
                        {"node_id": nid, "score": score} for nid, score in top_degree
                    ],
                    "betweenness": [
                        {"node_id": nid, "score": score}
                        for nid, score in top_betweenness
                    ],
                    "closeness": [
                        {"node_id": nid, "score": score} for nid, score in top_closeness
                    ],
                    "pagerank": [
                        {"node_id": nid, "score": score} for nid, score in top_pagerank
                    ],
                },
            )

            # Store analysis results
            self._store_analysis_result(network_id, "comprehensive_analysis", result)

            logger.info(
                f"Network analysis complete: {total_nodes} nodes, {total_edges} edges, density: {density:.3f}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to analyze network: {e}")
            # Return basic result
            return NetworkAnalysisResult(
                network_type=NetworkType.CITATION,
                metrics=NetworkMetrics(0, 0, 0, 0, 0, 0, 0, 0),
                top_nodes=[],
                communities=[],
                central_nodes={},
            )

    def _basic_network_analysis(
        self,
        network_id: int,
        nodes: Dict[str, NetworkNode],
        edges: List[NetworkEdge],
        network_type: NetworkType,
    ) -> NetworkAnalysisResult:
        """Basic network analysis without NetworkX."""
        logger.info("Performing basic network analysis (NetworkX not available)")

        try:
            total_nodes = len(nodes)
            total_edges = len(edges)
            density = (
                (2 * total_edges) / (total_nodes * (total_nodes - 1))
                if total_nodes > 1
                else 0
            )

            # Basic degree calculation
            degree_count = {}
            for edge in edges:
                degree_count[edge.source] = degree_count.get(edge.source, 0) + 1
                degree_count[edge.target] = degree_count.get(edge.target, 0) + 1

            # Find top nodes by degree
            top_by_degree = sorted(
                degree_count.items(), key=lambda x: x[1], reverse=True
            )[:10]

            top_nodes = []
            for node_id, degree in top_by_degree[:5]:
                node_data = nodes.get(node_id)
                top_nodes.append(
                    {
                        "node_id": node_id,
                        "label": node_data.label if node_data else node_id,
                        "degree": degree,
                        "degree_centrality": degree / (total_nodes - 1)
                        if total_nodes > 1
                        else 0,
                    }
                )

            metrics = NetworkMetrics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                density=density,
                clustering_coefficient=0,  # Not calculated without NetworkX
                average_path_length=0,  # Not calculated without NetworkX
                diameter=0,  # Not calculated without NetworkX
                connected_components=1,  # Assumed
                largest_component_size=total_nodes,
            )

            result = NetworkAnalysisResult(
                network_type=network_type,
                metrics=metrics,
                top_nodes=top_nodes,
                communities=[],
                central_nodes={
                    "degree": [
                        {"node_id": nid, "score": score} for nid, score in top_by_degree
                    ]
                },
            )

            self._store_analysis_result(network_id, "basic_analysis", result)

            logger.info(
                f"Basic network analysis complete: {total_nodes} nodes, {total_edges} edges"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to perform basic network analysis: {e}")
            return NetworkAnalysisResult(
                network_type=network_type,
                metrics=NetworkMetrics(0, 0, 0, 0, 0, 0, 0, 0),
                top_nodes=[],
                communities=[],
                central_nodes={},
            )

    def get_shortest_path(self, network_id: int, source: str, target: str) -> List[str]:
        """Find shortest path between two nodes."""
        if not NETWORKX_AVAILABLE:
            logger.warning(
                "NetworkX not available. Shortest path calculation not supported."
            )
            return []

        try:
            nodes, edges, _ = self._load_network_data(network_id)

            # Create NetworkX graph
            G = networkx.Graph()
            for node in nodes.values():
                G.add_node(node.node_id)
            for edge in edges:
                G.add_edge(edge.source, edge.target, weight=edge.weight)

            path = networkx.shortest_path(G, source, target)
            return path

        except Exception as e:
            logger.error(f"Failed to find shortest path: {e}")
            return []

    def find_influential_nodes(
        self, network_id: int, top_k: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find most influential nodes using various centrality measures."""
        logger.info(f"Finding top {top_k} influential nodes in network {network_id}")

        try:
            # Get or perform analysis
            analysis_result = self.analyze_network(network_id)

            if analysis_result.central_nodes:
                # Limit to top_k for each measure
                influential = {}
                for measure, nodes in analysis_result.central_nodes.items():
                    influential[measure] = nodes[:top_k]

                return influential
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to find influential nodes: {e}")
            return {}

    def _store_network_data(
        self, network_id: int, nodes: Dict[str, NetworkNode], edges: List[NetworkEdge]
    ) -> None:
        """Store network data in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store nodes
                for node in nodes.values():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO network_nodes
                        (network_id, node_id, node_type, label, attributes, centrality_scores)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            network_id,
                            node.node_id,
                            node.node_type,
                            node.label,
                            json.dumps(node.attributes),
                            json.dumps(node.centrality_scores),
                        ),
                    )

                # Store edges
                for edge in edges:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO network_edges
                        (network_id, source, target, weight, edge_type, attributes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            network_id,
                            edge.source,
                            edge.target,
                            edge.weight,
                            edge.edge_type,
                            json.dumps(edge.attributes),
                        ),
                    )

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store network data: {e}")

    def _load_network_data(
        self, network_id: int
    ) -> Tuple[Dict[str, NetworkNode], List[NetworkEdge], str]:
        """Load network data from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get network type
                cursor = conn.execute(
                    """
                    SELECT network_type FROM networks WHERE id = ?
                """,
                    (network_id,),
                )
                row = cursor.fetchone()
                network_type = row[0] if row else "unknown"

                # Load nodes
                cursor = conn.execute(
                    """
                    SELECT node_id, node_type, label, attributes, centrality_scores
                    FROM network_nodes WHERE network_id = ?
                """,
                    (network_id,),
                )

                nodes = {}
                for (
                    node_id,
                    node_type,
                    label,
                    attributes_str,
                    centrality_str,
                ) in cursor.fetchall():
                    attributes = json.loads(attributes_str) if attributes_str else {}
                    centrality_scores = (
                        json.loads(centrality_str) if centrality_str else {}
                    )

                    nodes[node_id] = NetworkNode(
                        node_id=node_id,
                        node_type=node_type,
                        label=label,
                        attributes=attributes,
                        centrality_scores=centrality_scores,
                    )

                # Load edges
                cursor = conn.execute(
                    """
                    SELECT source, target, weight, edge_type, attributes
                    FROM network_edges WHERE network_id = ?
                """,
                    (network_id,),
                )

                edges = []
                for (
                    source,
                    target,
                    weight,
                    edge_type,
                    attributes_str,
                ) in cursor.fetchall():
                    attributes = json.loads(attributes_str) if attributes_str else {}

                    edges.append(
                        NetworkEdge(
                            source=source,
                            target=target,
                            weight=weight,
                            edge_type=edge_type,
                            attributes=attributes,
                        )
                    )

                return nodes, edges, network_type

        except Exception as e:
            logger.error(f"Failed to load network data: {e}")
            return {}, [], "unknown"

    def _store_analysis_result(
        self, network_id: int, analysis_type: str, result: NetworkAnalysisResult
    ) -> None:
        """Store analysis results in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Convert result to dict for JSON serialization
                result_dict = {
                    "network_type": result.network_type.value,
                    "metrics": {
                        "total_nodes": result.metrics.total_nodes,
                        "total_edges": result.metrics.total_edges,
                        "density": result.metrics.density,
                        "clustering_coefficient": result.metrics.clustering_coefficient,
                        "average_path_length": result.metrics.average_path_length,
                        "diameter": result.metrics.diameter,
                        "connected_components": result.metrics.connected_components,
                        "largest_component_size": result.metrics.largest_component_size,
                    },
                    "top_nodes": result.top_nodes,
                    "communities": result.communities,
                    "central_nodes": result.central_nodes,
                    "analysis_timestamp": result.analysis_timestamp.isoformat(),
                }

                conn.execute(
                    """
                    INSERT INTO network_analysis_results (network_id, analysis_type, results)
                    VALUES (?, ?, ?)
                """,
                    (network_id, analysis_type, json.dumps(result_dict)),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store analysis result: {e}")

    def get_network_list(self) -> List[Dict[str, Any]]:
        """Get list of all networks in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, network_type, network_name, created_at, metadata
                    FROM networks ORDER BY created_at DESC
                """
                )

                networks = []
                for (
                    network_id,
                    network_type,
                    network_name,
                    created_at,
                    metadata_str,
                ) in cursor.fetchall():
                    metadata = json.loads(metadata_str) if metadata_str else {}

                    networks.append(
                        {
                            "id": network_id,
                            "type": network_type,
                            "name": network_name,
                            "created_at": created_at,
                            "metadata": metadata,
                        }
                    )

                return networks

        except Exception as e:
            logger.error(f"Failed to get network list: {e}")
            return []

    def create_network(
        self,
        nodes: List[NetworkNode],
        edges: List[NetworkEdge],
        network_type: NetworkType,
    ) -> Any:
        """
        Create a network from nodes and edges for testing purposes.

        Args:
            nodes: List of network nodes
            edges: List of network edges
            network_type: Type of network to create

        Returns:
            Network object (NetworkX graph if available, else simple dict)
        """
        if not NETWORKX_AVAILABLE:
            logger.warning(
                "NetworkX not available. Returning simplified network representation."
            )
            return {
                "nodes": {node.node_id: node for node in nodes},
                "edges": edges,
                "type": network_type.value,
                "node_count": len(nodes),
                "edge_count": len(edges),
            }

        try:
            # Use the safe import
            import_result = safe_import("networkx")
            if import_result is None:
                return None

            # Create NetworkX graph
            if network_type in [NetworkType.CITATION, NetworkType.TOPIC]:
                graph = (
                    import_result.DiGraph()
                )  # Directed graph for citations and topics
            else:
                graph = import_result.Graph()  # Undirected graph for collaborations

            # Add nodes
            for node in nodes:
                graph.add_node(
                    node.node_id,
                    type=node.node_type,
                    label=node.label,
                    **node.attributes,
                )

            # Add edges
            for edge in edges:
                graph.add_edge(
                    edge.source,
                    edge.target,
                    weight=edge.weight,
                    edge_type=edge.edge_type,
                    **edge.attributes,
                )

            return graph

        except Exception as e:
            logger.error(f"Failed to create network: {e}")
            return None

    def analyze_network_from_data(
        self,
        nodes: List[NetworkNode],
        edges: List[NetworkEdge],
        network_type: NetworkType,
    ) -> Dict[str, Any]:
        """
        Analyze a network from direct node/edge input (separate method to avoid conflicts).

        Args:
            nodes: List of network nodes
            edges: List of network edges
            network_type: Network type

        Returns:
            Analysis results as dictionary
        """
        try:
            # Create the network
            network = self.create_network(nodes, edges, network_type)

            if network is None:
                return {"error": "Failed to create network"}

            # Basic analysis
            analysis_result = {
                "network_type": network_type.value,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # Add NetworkX-specific analysis if available
            if NETWORKX_AVAILABLE and hasattr(network, "number_of_nodes"):
                try:
                    nx = safe_import("networkx")
                    if nx:
                        analysis_result.update(
                            {
                                "density": nx.density(network),
                                "is_connected": (
                                    nx.is_connected(network)
                                    if not network.is_directed()
                                    else nx.is_strongly_connected(network)
                                ),
                                "average_clustering": (
                                    nx.average_clustering(network)
                                    if len(nodes) > 0
                                    else 0
                                ),
                            }
                        )
                except Exception as e:
                    logger.warning(f"NetworkX analysis failed: {e}")

            return analysis_result

        except Exception as e:
            logger.error(f"Failed to analyze direct network: {e}")
            return {"error": str(e)}


# Convenience functions
def create_network_analyzer(cache_dir: Optional[str] = None) -> NetworkAnalyzer:
    """Create a network analyzer instance."""
    return NetworkAnalyzer(cache_dir)


def quick_citation_network_analysis(
    papers: List[Dict[str, Any]],
) -> NetworkAnalysisResult:
    """Quick citation network analysis."""
    analyzer = create_network_analyzer()
    network_id = analyzer.create_citation_network(papers)
    if network_id > 0:
        return analyzer.analyze_network(network_id)
    else:
        return NetworkAnalysisResult(
            network_type=NetworkType.CITATION,
            metrics=NetworkMetrics(0, 0, 0, 0, 0, 0, 0, 0),
            top_nodes=[],
            communities=[],
            central_nodes={},
        )


if __name__ == "__main__":
    # Test basic functionality when run directly
    analyzer = create_network_analyzer()

    # Sample test data
    test_papers = [
        {
            "id": "paper1",
            "title": "Machine Learning Basics",
            "authors": ["Alice", "Bob"],
            "citations": ["paper2", "paper3"],
        },
        {
            "id": "paper2",
            "title": "Deep Learning Advanced",
            "authors": ["Bob", "Charlie"],
            "citations": ["paper3"],
        },
        {
            "id": "paper3",
            "title": "Neural Networks",
            "authors": ["Charlie", "Alice"],
            "citations": [],
        },
    ]

    # Create and analyze citation network
    citation_network_id = analyzer.create_citation_network(test_papers)
    citation_analysis = analyzer.analyze_network(citation_network_id)

    # Create and analyze collaboration network
    collab_network_id = analyzer.create_collaboration_network(test_papers)
    collab_analysis = analyzer.analyze_network(collab_network_id)

    print(
        f"Citation network: {citation_analysis.metrics.total_nodes} nodes, "
        f"{citation_analysis.metrics.total_edges} edges"
    )
    print(
        f"Collaboration network: {collab_analysis.metrics.total_nodes} nodes, "
        f"{collab_analysis.metrics.total_edges} edges"
    )
