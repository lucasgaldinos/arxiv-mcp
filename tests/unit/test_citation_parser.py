"""
Test suite for citation parser module.

This module tests the citation_parser wrapper functionality and imports.
"""

import pytest
import importlib.util
import sys


class TestCitationParser:
    """Test citation parser wrapper functionality."""

    def test_citation_parser_import(self):
        """Test that CitationParser can be imported successfully."""
        # This exercises the import statements in citation_parser.py
        from arxiv_mcp.parsers.citation_parser import CitationParser
        assert CitationParser is not None
        assert hasattr(CitationParser, '__init__')

    def test_citation_parser_instantiation(self):
        """Test that CitationParser can be instantiated."""
        # This exercises the re-export functionality
        from arxiv_mcp.parsers.citation_parser import CitationParser
        parser = CitationParser()
        assert parser is not None

    def test_citation_parser_wrapper_functionality(self):
        """Test that the wrapper provides expected methods."""
        from arxiv_mcp.parsers.citation_parser import CitationParser
        parser = CitationParser()
        # Verify it has the expected methods from the wrapped implementation
        assert hasattr(parser, 'extract_citations')
        assert callable(getattr(parser, 'extract_citations'))

    def test_citation_parser_all_exports(self):
        """Test that __all__ exports are correctly defined."""
        import arxiv_mcp.parsers.citation_parser as citation_parser
        assert hasattr(citation_parser, '__all__')
        assert 'CitationParser' in citation_parser.__all__
        
    def test_citation_parser_module_imports(self):
        """Test that all module-level imports work correctly."""
        # Import the module to execute all its lines
        import arxiv_mcp.parsers.citation_parser
        # Check that the re-export works
        assert hasattr(arxiv_mcp.parsers.citation_parser, 'CitationParser')
        # Check that __all__ is defined
        assert hasattr(arxiv_mcp.parsers.citation_parser, '__all__')
        
    def test_module_execution_with_spec(self):
        """Test module execution using importlib to ensure line coverage."""
        # Force reload of the module to ensure execution tracking
        import arxiv_mcp.parsers.citation_parser
        importlib.reload(arxiv_mcp.parsers.citation_parser)
        
        # Verify the module executed correctly
        assert hasattr(arxiv_mcp.parsers.citation_parser, 'CitationParser')
        assert hasattr(arxiv_mcp.parsers.citation_parser, '__all__')
        
        # Test the actual re-export
        from arxiv_mcp.parsers.citation_parser import CitationParser
        assert CitationParser is not None
        
        # Verify it's the same as the wrapped class
        from arxiv_mcp.utils.citations import CitationParser as OriginalParser
        assert CitationParser is OriginalParser