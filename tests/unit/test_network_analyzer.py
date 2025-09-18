"""
Test suite for network analyzer module.

This module tests the network_analyzer wrapper functionality and imports.
"""


class TestNetworkAnalyzer:
    """Test network analyzer wrapper functionality."""

    def test_network_analyzer_import(self):
        """Test that NetworkAnalyzer can be imported successfully."""
        # This exercises the import statements in network_analyzer.py
        from arxiv_mcp.analyzers.network_analyzer import NetworkAnalyzer

        assert NetworkAnalyzer is not None
        assert hasattr(NetworkAnalyzer, "__init__")

    def test_network_analyzer_instantiation(self):
        """Test that NetworkAnalyzer can be instantiated."""
        # This exercises the re-export functionality
        from arxiv_mcp.analyzers.network_analyzer import NetworkAnalyzer

        analyzer = NetworkAnalyzer()
        assert analyzer is not None

    def test_network_components_import(self):
        """Test that all network components can be imported."""
        # This exercises all the import and re-export statements
        from arxiv_mcp.analyzers.network_analyzer import NetworkEdge, NetworkNode, NetworkType

        assert NetworkNode is not None
        assert NetworkEdge is not None
        assert NetworkType is not None

    def test_network_analyzer_wrapper_functionality(self):
        """Test that the wrapper provides expected methods."""
        from arxiv_mcp.analyzers.network_analyzer import NetworkAnalyzer

        analyzer = NetworkAnalyzer()
        # Verify it has expected methods from the wrapped implementation
        assert hasattr(analyzer, "create_citation_network")
        assert callable(analyzer.create_citation_network)

    def test_network_analyzer_all_exports(self):
        """Test that __all__ exports are correctly defined."""
        from arxiv_mcp.analyzers import network_analyzer

        assert hasattr(network_analyzer, "__all__")
        expected_exports = ["NetworkAnalyzer", "NetworkNode", "NetworkEdge", "NetworkType"]
        for export in expected_exports:
            assert export in network_analyzer.__all__

    def test_network_type_enum_functionality(self):
        """Test that NetworkType enum is properly wrapped."""
        # This ensures the NetworkType import works correctly
        from arxiv_mcp.analyzers.network_analyzer import NetworkType

        assert NetworkType is not None
        # Basic verification that it behaves like an enum
        assert hasattr(NetworkType, "__members__")

    def test_network_analyzer_module_imports(self):
        """Test that all module-level imports work correctly."""
        # Import the module to execute all its lines
        import arxiv_mcp.analyzers.network_analyzer

        # Check that all re-exports work
        assert hasattr(arxiv_mcp.analyzers.network_analyzer, "NetworkAnalyzer")
        assert hasattr(arxiv_mcp.analyzers.network_analyzer, "NetworkNode")
        assert hasattr(arxiv_mcp.analyzers.network_analyzer, "NetworkEdge")
        assert hasattr(arxiv_mcp.analyzers.network_analyzer, "NetworkType")
        # Check that __all__ is defined
        assert hasattr(arxiv_mcp.analyzers.network_analyzer, "__all__")
