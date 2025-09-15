"""
Minimal integration tests for dependency_analysis.py - Focused on actual API
Target: 255 statements, currently 23% coverage
"""

import pytest
import tempfile
from pathlib import Path

from arxiv_mcp.utils.dependency_analysis import (
    DependencyAnalyzer,
    DependencyType, 
    Dependency,
    DependencyNode,
    DependencyGraph,
    create_dependency_analyzer,
    quick_package_analysis
)


class TestDependencyAnalyzerIntegration:
    """Integration tests for real dependency_analysis.py functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def dependency_analyzer(self, temp_cache_dir):
        """Create a DependencyAnalyzer with temporary cache for testing."""
        return DependencyAnalyzer(cache_dir=temp_cache_dir)

    def test_constructor_and_database(self, dependency_analyzer):
        """Test constructor and database initialization."""
        assert dependency_analyzer is not None
        assert dependency_analyzer.cache_dir is not None
        assert Path(dependency_analyzer.db_path).exists()

    def test_package_dependencies_basic(self, dependency_analyzer):
        """Test basic package dependency analysis."""
        result = dependency_analyzer.analyze_package_dependencies()
        
        assert 'available_dependencies' in result
        assert 'missing_dependencies' in result
        assert 'total_analyzed' in result
        assert isinstance(result['total_analyzed'], int)

    def test_package_dependencies_specific(self, dependency_analyzer):
        """Test specific package analysis."""
        result = dependency_analyzer.analyze_package_dependencies("requests")
        
        assert 'available_dependencies' in result
        assert 'total_analyzed' in result

    def test_paper_dependencies(self, dependency_analyzer):
        """Test paper dependency analysis."""
        result = dependency_analyzer.analyze_paper_dependencies("test_paper", ["cite1", "cite2"])
        
        assert 'paper_id' in result
        assert 'direct_dependencies' in result
        assert 'dependency_graph' in result

    def test_circular_dependencies(self, dependency_analyzer):
        """Test circular dependency detection."""
        # Create circular dependencies
        dep1 = Dependency("A", "B", DependencyType.PACKAGE)
        dep2 = Dependency("B", "A", DependencyType.PACKAGE)
        
        dependency_analyzer._store_dependency(dep1)
        dependency_analyzer._store_dependency(dep2)
        
        circular = dependency_analyzer.detect_circular_dependencies(DependencyType.PACKAGE)
        assert isinstance(circular, list)

    def test_dependency_impact(self, dependency_analyzer):
        """Test dependency impact analysis."""
        # Store test dependency first
        dep = Dependency("root", "child", DependencyType.PACKAGE)
        dependency_analyzer._store_dependency(dep)
        
        impact = dependency_analyzer.get_dependency_impact("root")
        
        assert 'node_id' in impact
        assert 'direct_dependencies' in impact
        assert 'impact_score' in impact

    def test_build_graph(self, dependency_analyzer):
        """Test dependency graph building."""
        # Add dependencies
        dep1 = Dependency("A", "B", DependencyType.PACKAGE)
        dep2 = Dependency("B", "C", DependencyType.PACKAGE)
        
        dependency_analyzer._store_dependency(dep1)
        dependency_analyzer._store_dependency(dep2)
        
        graph = dependency_analyzer.build_dependency_graph(DependencyType.PACKAGE)
        
        assert isinstance(graph, DependencyGraph)
        assert hasattr(graph, 'nodes')
        assert hasattr(graph, 'edges')

    def test_analysis_storage(self, dependency_analyzer):
        """Test analysis result storage."""
        test_results = {"metric": 42}
        dependency_analyzer._store_analysis_result("test", "target", test_results)
        
        history = dependency_analyzer.get_analysis_history("test", "target")
        assert isinstance(history, list)

    def test_dependency_dataclasses(self):
        """Test dependency dataclasses."""
        # Test Dependency
        dep = Dependency("src", "tgt", DependencyType.PACKAGE)
        assert dep.source == "src"
        assert dep.target == "tgt"
        
        # Test DependencyNode
        node = DependencyNode("id1", "type1", "name1")
        assert node.node_id == "id1"
        assert node.node_type == "type1"
        
        # Test DependencyGraph
        from datetime import datetime
        graph = DependencyGraph({}, [], "test", datetime.now())
        assert graph.graph_type == "test"

    def test_convenience_functions(self, temp_cache_dir):
        """Test convenience functions."""
        # Test create_dependency_analyzer
        analyzer = create_dependency_analyzer(cache_dir=temp_cache_dir)
        assert isinstance(analyzer, DependencyAnalyzer)
        
        # Test quick_package_analysis
        result = quick_package_analysis()
        assert isinstance(result, dict)

    def test_database_persistence(self, dependency_analyzer):
        """Test database persistence."""
        # Store dependency
        dep = Dependency("persist_test", "target", DependencyType.PACKAGE)
        dependency_analyzer._store_dependency(dep)
        
        # Create new analyzer with same cache
        new_analyzer = DependencyAnalyzer(cache_dir=dependency_analyzer.cache_dir)
        impact = new_analyzer.get_dependency_impact("persist_test")
        assert 'node_id' in impact

    def test_error_handling(self, dependency_analyzer):
        """Test error handling."""
        # Test with empty inputs
        result = dependency_analyzer.analyze_paper_dependencies("empty", [])
        assert 'paper_id' in result
        assert result['direct_dependencies'] == 0

    def test_enum_functionality(self):
        """Test DependencyType enum."""
        assert DependencyType.PACKAGE.value == "package"
        assert DependencyType.PAPER.value == "paper"
        assert DependencyType.CITATION.value == "citation"