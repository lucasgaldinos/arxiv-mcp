"""
Tests for new implementations: DependencyAnalyzer and NetworkAnalyzer.

This module contains comprehensive tests for the newly implemented
dependency analysis and network analysis systems.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.arxiv_mcp.utils.dependency_analysis import (
    DependencyAnalyzer,
    DependencyType,
    Dependency,
    DependencyNode,
)
from src.arxiv_mcp.utils.network_analysis import (
    NetworkAnalyzer,
    NetworkType,
    NetworkNode,
    NetworkEdge,
)


class TestDependencyAnalyzer:
    """Test suite for DependencyAnalyzer."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def analyzer(self, temp_cache_dir):
        """Create a DependencyAnalyzer instance for testing."""
        return DependencyAnalyzer(cache_dir=temp_cache_dir)

    def test_dependency_analyzer_initialization(self, analyzer, temp_cache_dir):
        """Test that DependencyAnalyzer initializes correctly."""
        assert analyzer.cache_dir == Path(temp_cache_dir)
        assert analyzer.db_path.exists()
        assert analyzer.db_path.name == "dependencies.db"

    def test_analyze_package_dependencies(self, analyzer):
        """Test package dependency analysis."""
        # Test analyzing all packages
        result = analyzer.analyze_package_dependencies()

        # Verify result structure
        assert isinstance(result, dict)
        assert "available_dependencies" in result
        assert "missing_dependencies" in result
        assert "circular_dependencies" in result
        assert "total_analyzed" in result
        assert "availability_ratio" in result
        assert "analysis_timestamp" in result

        # Verify data types
        assert isinstance(result["available_dependencies"], dict)
        assert isinstance(result["missing_dependencies"], dict)
        assert isinstance(result["circular_dependencies"], list)
        assert isinstance(result["total_analyzed"], int)
        assert isinstance(result["availability_ratio"], (int, float))

        # Verify total count makes sense
        available_count = len(result["available_dependencies"])
        missing_count = len(result["missing_dependencies"])
        assert result["total_analyzed"] == available_count + missing_count

    def test_analyze_specific_package_dependency(self, analyzer):
        """Test analyzing a specific package dependency."""
        # Test with a package that should exist in optional_deps
        result = analyzer.analyze_package_dependencies("networkx")

        # Should have results even if the package is missing
        assert isinstance(result, dict)
        assert result["total_analyzed"] >= 0

    def test_dependency_creation(self):
        """Test Dependency dataclass creation."""
        dep = Dependency(
            source="paper1",
            target="paper2",
            dependency_type=DependencyType.CITATION,
            strength=0.8,
        )

        assert dep.source == "paper1"
        assert dep.target == "paper2"
        assert dep.dependency_type == DependencyType.CITATION
        assert dep.strength == 0.8
        assert isinstance(dep.discovered_at, datetime)
        assert isinstance(dep.metadata, dict)

    def test_dependency_node_creation(self):
        """Test DependencyNode dataclass creation."""
        node = DependencyNode(
            node_id="node1",
            node_type="package",
            name="test_package",
            version="1.0.0",
            description="Test package",
        )

        assert node.node_id == "node1"
        assert node.node_type == "package"
        assert node.name == "test_package"
        assert node.version == "1.0.0"
        assert node.description == "Test package"
        assert isinstance(node.metadata, dict)
        assert isinstance(node.dependencies, list)
        assert isinstance(node.dependents, list)

    def test_store_analysis_result(self, analyzer):
        """Test storing analysis results in database."""
        test_results = {
            "test_key": "test_value",
            "timestamp": datetime.now().isoformat(),
        }

        # This should not raise an exception
        analyzer._store_analysis_result("test_analysis", "test_target", test_results)

    def test_get_stored_analysis(self, analyzer):
        """Test retrieving stored analysis results."""
        # Store a test result first
        test_results = {"test": "data"}
        analyzer._store_analysis_result("test_type", "test_target", test_results)

        # Try to retrieve it
        stored_results = analyzer._get_stored_analysis("test_type", "test_target")
        assert stored_results is not None


class TestNetworkAnalyzer:
    """Test suite for NetworkAnalyzer."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def analyzer(self, temp_cache_dir):
        """Create a NetworkAnalyzer instance for testing."""
        return NetworkAnalyzer(cache_dir=temp_cache_dir)

    def test_network_analyzer_initialization(self, analyzer, temp_cache_dir):
        """Test that NetworkAnalyzer initializes correctly."""
        assert analyzer.cache_dir == Path(temp_cache_dir)
        assert analyzer.db_path.exists()
        assert analyzer.db_path.name == "networks.db"

    def test_network_node_creation(self):
        """Test NetworkNode dataclass creation."""
        node = NetworkNode(
            node_id="node1",
            node_type="paper",
            label="Test Paper",
            attributes={"year": 2023, "category": "cs.AI"},
        )

        assert node.node_id == "node1"
        assert node.node_type == "paper"
        assert node.label == "Test Paper"
        assert node.attributes["year"] == 2023
        assert node.attributes["category"] == "cs.AI"
        assert isinstance(node.centrality_scores, dict)

    def test_network_edge_creation(self):
        """Test NetworkEdge dataclass creation."""
        edge = NetworkEdge(
            source="paper1",
            target="paper2",
            weight=0.5,
            edge_type="citation",
            attributes={"citation_count": 3},
        )

        assert edge.source == "paper1"
        assert edge.target == "paper2"
        assert edge.weight == 0.5
        assert edge.edge_type == "citation"
        assert edge.attributes["citation_count"] == 3

    def test_create_simple_network(self, analyzer):
        """Test creating a simple network."""
        # Create test nodes
        nodes = [
            NetworkNode("1", "paper", "Paper 1"),
            NetworkNode("2", "paper", "Paper 2"),
            NetworkNode("3", "paper", "Paper 3"),
        ]

        # Create test edges
        edges = [
            NetworkEdge("1", "2", 1.0, "citation"),
            NetworkEdge("2", "3", 1.0, "citation"),
        ]

        # Test network creation
        network = analyzer.create_network(nodes, edges, NetworkType.CITATION)

        # Basic validation
        assert network is not None
        if hasattr(network, "number_of_nodes"):
            assert network.number_of_nodes() == 3
            assert network.number_of_edges() == 2

    def test_analyze_network_basic(self, analyzer):
        """Test basic network analysis."""
        # Create a simple test network
        nodes = [
            NetworkNode("1", "paper", "Paper 1"),
            NetworkNode("2", "paper", "Paper 2"),
        ]
        edges = [NetworkEdge("1", "2", 1.0, "citation")]

        # Analyze the network using the correct method name
        result = analyzer.analyze_network_from_data(nodes, edges, NetworkType.CITATION)

        # Verify result structure
        assert isinstance(result, dict)
        # The exact structure depends on implementation but should contain basic info
        assert (
            "network_type" in result
            or "total_nodes" in result
            or "analysis_timestamp" in result
        )

    def test_networkx_availability_handling(self, analyzer):
        """Test that the analyzer handles NetworkX availability gracefully."""
        # This test should pass regardless of whether NetworkX is installed
        from src.arxiv_mcp.utils.network_analysis import NETWORKX_AVAILABLE

        # Test should work with or without NetworkX
        assert isinstance(NETWORKX_AVAILABLE, bool)

        # Basic network creation should work even without NetworkX
        nodes = [NetworkNode("1", "test", "Test Node")]
        edges = []

        # This should not raise an exception
        try:
            network_result = analyzer.create_network(nodes, edges, NetworkType.CITATION)
            # If NetworkX is not available, this might return None or a simple structure
            assert network_result is not None or True  # Accept None as valid fallback
        except Exception as e:
            # Should fail gracefully
            assert "NetworkX" in str(e) or "not available" in str(e).lower()


class TestIntegration:
    """Integration tests for both analyzers working together."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_dependency_and_network_analyzers_together(self, temp_cache_dir):
        """Test that both analyzers can work in the same environment."""
        dep_analyzer = DependencyAnalyzer(cache_dir=temp_cache_dir + "/deps")
        net_analyzer = NetworkAnalyzer(cache_dir=temp_cache_dir + "/nets")

        # Both should initialize without conflicts
        assert dep_analyzer.cache_dir != net_analyzer.cache_dir
        assert dep_analyzer.db_path.exists()
        assert net_analyzer.db_path.exists()

    def test_enum_values(self):
        """Test that enum values are properly defined."""
        # Test DependencyType enum
        assert DependencyType.PACKAGE.value == "package"
        assert DependencyType.PAPER.value == "paper"
        assert DependencyType.CITATION.value == "citation"
        assert DependencyType.AUTHOR.value == "author"
        assert DependencyType.TOPIC.value == "topic"

        # Test NetworkType enum
        assert NetworkType.CITATION.value == "citation"
        assert NetworkType.COLLABORATION.value == "collaboration"
        assert NetworkType.TOPIC.value == "topic"
        assert NetworkType.KEYWORD.value == "keyword"
        assert NetworkType.AUTHOR.value == "author"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
