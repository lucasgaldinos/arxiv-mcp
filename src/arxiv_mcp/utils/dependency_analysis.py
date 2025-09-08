"""
Dependency Analysis System for ArXiv MCP

This module provides comprehensive dependency analysis capabilities including
package dependencies, paper dependencies, and cross-reference analysis.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .logging import structured_logger
from .optional_deps import OPTIONAL_DEPS


logger = structured_logger()


class DependencyType(Enum):
    """Types of dependencies that can be analyzed."""

    PACKAGE = "package"
    PAPER = "paper"
    CITATION = "citation"
    AUTHOR = "author"
    TOPIC = "topic"


@dataclass
class Dependency:
    """Represents a dependency relationship."""

    source: str
    target: str
    dependency_type: DependencyType
    strength: float = 1.0
    metadata: Dict[str, Any] = None
    discovered_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.discovered_at is None:
            self.discovered_at = datetime.now()


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""

    node_id: str
    node_type: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    dependencies: List[str] = None
    dependents: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []


@dataclass
class DependencyGraph:
    """Represents a complete dependency graph."""

    nodes: Dict[str, DependencyNode]
    edges: List[Dependency]
    graph_type: str
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DependencyAnalyzer:
    """
    Comprehensive dependency analysis system.

    Features:
    - Package dependency analysis
    - Paper citation dependencies
    - Author collaboration dependencies
    - Topic relationship analysis
    - Dependency graph construction
    - Circular dependency detection
    - Impact analysis
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the dependency analyzer."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path.cwd() / "dependency_cache"
        )
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "dependencies.db"
        self._init_database()

        logger.info(f"DependencyAnalyzer initialized with cache: {self.cache_dir}")

    def _init_database(self) -> None:
        """Initialize SQLite database for dependency tracking."""
        with sqlite3.connect(self.db_path) as conn:
            # Dependencies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    metadata TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, target, dependency_type)
                )
            """)

            # Nodes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dependency_nodes (
                    node_id TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT,
                    description TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Analysis results table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def analyze_package_dependencies(self, package_name: str = None) -> Dict[str, Any]:
        """Analyze package dependencies using the optional dependencies system."""
        logger.info(
            f"Analyzing package dependencies for: {package_name or 'all packages'}"
        )

        try:
            # Analyze optional dependencies
            available_deps = {}
            missing_deps = {}
            circular_deps = []

            for name, dep in OPTIONAL_DEPS.items():
                if package_name and name != package_name:
                    continue

                # Check availability
                if dep.available:
                    available_deps[name] = {
                        "package": dep.package,
                        "feature": dep.feature,
                        "status": "available",
                        "import_path": dep.name,
                    }
                else:
                    missing_deps[name] = {
                        "package": dep.package,
                        "feature": dep.feature,
                        "status": "missing",
                        "import_path": dep.name,
                    }

            # Store analysis results
            analysis_results = {
                "available_dependencies": available_deps,
                "missing_dependencies": missing_deps,
                "circular_dependencies": circular_deps,
                "total_analyzed": len(available_deps) + len(missing_deps),
                "availability_ratio": len(available_deps)
                / (len(available_deps) + len(missing_deps))
                if available_deps or missing_deps
                else 0,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # Store in database
            self._store_analysis_result(
                "package_dependencies", package_name or "all", analysis_results
            )

            logger.info(
                f"Package dependency analysis complete: {len(available_deps)} available, {len(missing_deps)} missing"
            )
            return analysis_results

        except Exception as e:
            logger.error(f"Failed to analyze package dependencies: {e}")
            return {
                "error": str(e),
                "available_dependencies": {},
                "missing_dependencies": {},
            }

    def analyze_paper_dependencies(
        self, paper_id: str, citations: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze dependencies between papers based on citations."""
        logger.info(f"Analyzing paper dependencies for: {paper_id}")

        try:
            dependencies = []
            dependency_graph = {}

            if citations:
                for citation in citations:
                    # Create dependency relationship
                    dep = Dependency(
                        source=paper_id,
                        target=citation,
                        dependency_type=DependencyType.CITATION,
                        strength=1.0,
                        metadata={"relationship": "cites"},
                    )
                    dependencies.append(dep)

                    # Add to graph
                    if paper_id not in dependency_graph:
                        dependency_graph[paper_id] = {
                            "depends_on": [],
                            "depended_by": [],
                        }
                    dependency_graph[paper_id]["depends_on"].append(citation)

                    if citation not in dependency_graph:
                        dependency_graph[citation] = {
                            "depends_on": [],
                            "depended_by": [],
                        }
                    dependency_graph[citation]["depended_by"].append(paper_id)

            # Store dependencies in database
            for dep in dependencies:
                self._store_dependency(dep)

            analysis_results = {
                "paper_id": paper_id,
                "direct_dependencies": len(dependencies),
                "dependency_graph": dependency_graph,
                "citations_analyzed": len(citations) if citations else 0,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            self._store_analysis_result(
                "paper_dependencies", paper_id, analysis_results
            )

            logger.info(
                f"Paper dependency analysis complete: {len(dependencies)} dependencies found"
            )
            return analysis_results

        except Exception as e:
            logger.error(f"Failed to analyze paper dependencies: {e}")
            return {"error": str(e), "paper_id": paper_id, "direct_dependencies": 0}

    def detect_circular_dependencies(
        self, dependency_type: DependencyType
    ) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph."""
        logger.info(
            f"Detecting circular dependencies for type: {dependency_type.value}"
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get all dependencies of the specified type
                cursor = conn.execute(
                    """
                    SELECT source, target FROM dependencies 
                    WHERE dependency_type = ?
                """,
                    (dependency_type.value,),
                )

                edges = cursor.fetchall()

                # Build adjacency list
                graph = {}
                for source, target in edges:
                    if source not in graph:
                        graph[source] = []
                    graph[source].append(target)

                # Find cycles using DFS
                visited = set()
                rec_stack = set()
                cycles = []

                def dfs(node, path):
                    if node in rec_stack:
                        # Found cycle
                        cycle_start = path.index(node)
                        cycle = path[cycle_start:] + [node]
                        cycles.append(cycle)
                        return

                    if node in visited:
                        return

                    visited.add(node)
                    rec_stack.add(node)
                    path.append(node)

                    for neighbor in graph.get(node, []):
                        dfs(neighbor, path[:])

                    rec_stack.remove(node)
                    path.pop()

                # Check all nodes
                for node in graph.keys():
                    if node not in visited:
                        dfs(node, [])

                logger.info(
                    f"Circular dependency detection complete: {len(cycles)} cycles found"
                )
                return cycles

        except Exception as e:
            logger.error(f"Failed to detect circular dependencies: {e}")
            return []

    def get_dependency_impact(self, node_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Analyze the impact of a node in the dependency graph."""
        logger.info(f"Analyzing dependency impact for: {node_id}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get direct dependencies (things this node depends on)
                cursor = conn.execute(
                    """
                    SELECT target, dependency_type, strength FROM dependencies 
                    WHERE source = ?
                """,
                    (node_id,),
                )
                direct_dependencies = cursor.fetchall()

                # Get direct dependents (things that depend on this node)
                cursor = conn.execute(
                    """
                    SELECT source, dependency_type, strength FROM dependencies 
                    WHERE target = ?
                """,
                    (node_id,),
                )
                direct_dependents = cursor.fetchall()

                # Calculate impact metrics
                impact_score = len(direct_dependents) * 2 + len(direct_dependencies)

                # Get transitive dependencies (recursive dependencies)
                def get_transitive_deps(node, depth, visited):
                    if depth <= 0 or node in visited:
                        return []

                    visited.add(node)
                    deps = []

                    cursor = conn.execute(
                        """
                        SELECT target FROM dependencies WHERE source = ?
                    """,
                        (node,),
                    )

                    for (target,) in cursor.fetchall():
                        deps.append(target)
                        deps.extend(
                            get_transitive_deps(target, depth - 1, visited.copy())
                        )

                    return deps

                transitive_dependencies = get_transitive_deps(node_id, max_depth, set())

                impact_analysis = {
                    "node_id": node_id,
                    "direct_dependencies": len(direct_dependencies),
                    "direct_dependents": len(direct_dependents),
                    "transitive_dependencies": len(set(transitive_dependencies)),
                    "impact_score": impact_score,
                    "dependency_details": {
                        "depends_on": [
                            {"target": t, "type": dt, "strength": s}
                            for t, dt, s in direct_dependencies
                        ],
                        "depended_by": [
                            {"source": s, "type": dt, "strength": st}
                            for s, dt, st in direct_dependents
                        ],
                    },
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                self._store_analysis_result(
                    "dependency_impact", node_id, impact_analysis
                )

                logger.info(
                    f"Dependency impact analysis complete: impact score {impact_score}"
                )
                return impact_analysis

        except Exception as e:
            logger.error(f"Failed to analyze dependency impact: {e}")
            return {"error": str(e), "node_id": node_id, "impact_score": 0}

    def build_dependency_graph(
        self, dependency_type: DependencyType = None
    ) -> DependencyGraph:
        """Build a complete dependency graph."""
        logger.info(
            f"Building dependency graph for type: {dependency_type.value if dependency_type else 'all'}"
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get nodes
                if dependency_type:
                    cursor = conn.execute(
                        """
                        SELECT DISTINCT source FROM dependencies WHERE dependency_type = ?
                        UNION
                        SELECT DISTINCT target FROM dependencies WHERE dependency_type = ?
                    """,
                        (dependency_type.value, dependency_type.value),
                    )
                else:
                    cursor = conn.execute("""
                        SELECT DISTINCT source FROM dependencies
                        UNION
                        SELECT DISTINCT target FROM dependencies
                    """)

                node_ids = [row[0] for row in cursor.fetchall()]

                # Build nodes
                nodes = {}
                for node_id in node_ids:
                    # Try to get node details
                    cursor = conn.execute(
                        """
                        SELECT node_type, name, version, description, metadata 
                        FROM dependency_nodes WHERE node_id = ?
                    """,
                        (node_id,),
                    )

                    row = cursor.fetchone()
                    if row:
                        node_type, name, version, description, metadata_str = row
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    else:
                        # Create basic node
                        node_type = "unknown"
                        name = node_id
                        version = None
                        description = None
                        metadata = {}

                    nodes[node_id] = DependencyNode(
                        node_id=node_id,
                        node_type=node_type,
                        name=name,
                        version=version,
                        description=description,
                        metadata=metadata,
                    )

                # Get edges
                if dependency_type:
                    cursor = conn.execute(
                        """
                        SELECT source, target, dependency_type, strength, metadata, discovered_at
                        FROM dependencies WHERE dependency_type = ?
                    """,
                        (dependency_type.value,),
                    )
                else:
                    cursor = conn.execute("""
                        SELECT source, target, dependency_type, strength, metadata, discovered_at
                        FROM dependencies
                    """)

                edges = []
                for (
                    source,
                    target,
                    dep_type,
                    strength,
                    metadata_str,
                    discovered_at,
                ) in cursor.fetchall():
                    metadata = json.loads(metadata_str) if metadata_str else {}

                    edges.append(
                        Dependency(
                            source=source,
                            target=target,
                            dependency_type=DependencyType(dep_type),
                            strength=strength,
                            metadata=metadata,
                            discovered_at=datetime.fromisoformat(discovered_at)
                            if discovered_at
                            else None,
                        )
                    )

                graph = DependencyGraph(
                    nodes=nodes,
                    edges=edges,
                    graph_type=dependency_type.value if dependency_type else "mixed",
                    created_at=datetime.now(),
                    metadata={"total_nodes": len(nodes), "total_edges": len(edges)},
                )

                logger.info(
                    f"Dependency graph built: {len(nodes)} nodes, {len(edges)} edges"
                )
                return graph

        except Exception as e:
            logger.error(f"Failed to build dependency graph: {e}")
            return DependencyGraph(
                nodes={},
                edges=[],
                graph_type="error",
                created_at=datetime.now(),
                metadata={"error": str(e)},
            )

    def _store_dependency(self, dependency: Dependency) -> None:
        """Store a dependency in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dependencies 
                    (source, target, dependency_type, strength, metadata, discovered_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        dependency.source,
                        dependency.target,
                        dependency.dependency_type.value,
                        dependency.strength,
                        json.dumps(dependency.metadata),
                        dependency.discovered_at.isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store dependency: {e}")

    def _store_analysis_result(
        self, analysis_type: str, target_id: str, results: Dict[str, Any]
    ) -> None:
        """Store analysis results in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO analysis_results (analysis_type, target_id, results)
                    VALUES (?, ?, ?)
                """,
                    (analysis_type, target_id, json.dumps(results)),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store analysis result: {e}")

    def _get_stored_analysis(
        self, analysis_type: str, target_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent stored analysis result for a specific type and target."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT results FROM analysis_results 
                    WHERE analysis_type = ? AND target_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (analysis_type, target_id),
                )

                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None

        except Exception as e:
            logger.error(f"Failed to get stored analysis: {e}")
            return None

    def get_analysis_history(
        self, analysis_type: str = None, target_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get historical analysis results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if analysis_type and target_id:
                    cursor = conn.execute(
                        """
                        SELECT analysis_type, target_id, results, created_at
                        FROM analysis_results 
                        WHERE analysis_type = ? AND target_id = ?
                        ORDER BY created_at DESC
                    """,
                        (analysis_type, target_id),
                    )
                elif analysis_type:
                    cursor = conn.execute(
                        """
                        SELECT analysis_type, target_id, results, created_at
                        FROM analysis_results 
                        WHERE analysis_type = ?
                        ORDER BY created_at DESC
                    """,
                        (analysis_type,),
                    )
                else:
                    cursor = conn.execute("""
                        SELECT analysis_type, target_id, results, created_at
                        FROM analysis_results 
                        ORDER BY created_at DESC
                    """)

                results = []
                for (
                    analysis_type,
                    target_id,
                    results_str,
                    created_at,
                ) in cursor.fetchall():
                    results.append(
                        {
                            "analysis_type": analysis_type,
                            "target_id": target_id,
                            "results": json.loads(results_str),
                            "created_at": created_at,
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []


# Convenience functions
def create_dependency_analyzer(cache_dir: Optional[str] = None) -> DependencyAnalyzer:
    """Create a dependency analyzer instance."""
    return DependencyAnalyzer(cache_dir)


def quick_package_analysis() -> Dict[str, Any]:
    """Quick analysis of package dependencies."""
    analyzer = create_dependency_analyzer()
    return analyzer.analyze_package_dependencies()


if __name__ == "__main__":
    # Generate sample analysis when run directly
    analyzer = create_dependency_analyzer()
    results = analyzer.analyze_package_dependencies()

    print(f"Package dependency analysis: {results['total_analyzed']} packages analyzed")
    print(
        f"Available: {len(results['available_dependencies'])}, Missing: {len(results['missing_dependencies'])}"
    )
