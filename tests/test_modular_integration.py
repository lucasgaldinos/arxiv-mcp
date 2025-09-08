"""
Comprehensive test suite for the modular ArXiv MCP architecture.
Tests all major components and their interactions to ensure system integrity.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arxiv_mcp.utils.validation import ArxivValidator
from arxiv_mcp.utils.metrics import MetricsCollector
from arxiv_mcp.exceptions import (
    ArxivMCPError,
    DownloadError,
    ExtractionError,
    CompilationError,
)
from arxiv_mcp.core.enhanced_config import PipelineConfig
from arxiv_mcp.core.config import load_config
from arxiv_mcp.clients import AsyncArxivDownloader
from arxiv_mcp.processors import LaTeXProcessor, PDFProcessor
from arxiv_mcp.core.pipeline import ArxivPipeline


class TestArxivValidator:
    """Test the ArxivValidator utility class."""

    def test_valid_arxiv_ids(self):
        """Test validation of valid ArXiv IDs."""
        validator = ArxivValidator()

        # Test valid new format
        assert validator.validate_arxiv_id("2301.00001")

        # Test valid old format
        assert validator.validate_arxiv_id("math.GT/0601001")

    def test_invalid_arxiv_ids(self):
        """Test validation of invalid ArXiv IDs."""
        validator = ArxivValidator()

        # Test invalid formats
        assert not validator.validate_arxiv_id("invalid")
        assert not validator.validate_arxiv_id("")
        assert not validator.validate_arxiv_id("12345")
        assert not validator.validate_arxiv_id("2301")


class TestMetricsCollector:
    """Test the metrics collection functionality."""

    def test_metrics_initialization(self):
        """Test metrics collector initialization."""
        metrics = MetricsCollector()
        assert hasattr(metrics, "increment_counter")
        assert hasattr(metrics, "start_timer")
        assert hasattr(metrics, "end_timer")
        assert hasattr(metrics, "get_all_metrics")

    def test_counter_operations(self):
        """Test counter increment operations."""
        metrics = MetricsCollector()

        # Test basic counter increment
        metrics.increment_counter("test_counter")
        all_metrics = metrics.get_all_metrics()
        assert "test_counter" in all_metrics["counters"]
        assert all_metrics["counters"]["test_counter"] == 1

        # Test counter with labels
        metrics.increment_counter("test_counter", {"label": "value"})
        # Should create separate counter with labels


class TestExceptionHierarchy:
    """Test the custom exception hierarchy."""

    def test_base_exception(self):
        """Test the base ArxivMCPError exception."""
        base_error = ArxivMCPError("Base error")
        assert str(base_error) == "Base error"
        assert isinstance(base_error, Exception)

    def test_specific_exceptions(self):
        """Test specific exception types inherit from base."""
        download_error = DownloadError("Download failed")
        assert isinstance(download_error, ArxivMCPError)

        ext_error = ExtractionError("Extraction failed")
        assert isinstance(ext_error, ArxivMCPError)

        comp_error = CompilationError("Compilation failed")
        assert isinstance(comp_error, ArxivMCPError)


class TestPipelineConfig:
    """Test the pipeline configuration management."""

    def test_config_loading(self):
        """Test configuration loading from dictionary."""
        config_dict = load_config()
        assert isinstance(config_dict, dict)
        assert "max_downloads" in config_dict
        assert "requests_per_second" in config_dict

    def test_pipeline_config_creation(self):
        """Test PipelineConfig creation from dictionary."""
        config_dict = load_config()
        config = PipelineConfig.from_dict(config_dict)

        assert isinstance(config, PipelineConfig)
        assert config.max_downloads == config_dict["max_downloads"]
        assert config.requests_per_second == config_dict["requests_per_second"]
        assert config.enable_http_validation == config_dict["enable_http_validation"]


class TestAsyncArxivDownloader:
    """Test the async ArXiv downloader client."""

    @pytest.mark.asyncio
    async def test_downloader_initialization(self):
        """Test downloader initialization."""
        downloader = AsyncArxivDownloader()
        assert downloader.requests_per_second == 2.0
        assert downloader.burst_size == 5
        assert hasattr(downloader, "download")
        assert hasattr(downloader, "get_metadata")

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        downloader = AsyncArxivDownloader(requests_per_second=1.0, burst_size=2)

        # Test rate limiting mechanism exists
        assert hasattr(downloader, "_rate_limit")

        # Call rate limiting function
        await downloader._rate_limit()
        # Should not raise any exceptions


class TestLaTeXProcessor:
    """Test the LaTeX processor functionality."""

    def test_processor_initialization(self):
        """Test LaTeX processor initialization."""
        processor = LaTeXProcessor()
        assert hasattr(processor, "extract_archive")
        assert hasattr(processor, "find_main_tex_file")
        assert hasattr(processor, "extract_text_from_tex")

    def test_text_extraction(self):
        """Test LaTeX text extraction."""
        processor = LaTeXProcessor()

        # Test basic LaTeX text cleaning
        latex_text = r"""
        \documentclass{article}
        \begin{document}
        \title{Test Paper}
        \author{Test Author}
        This is some text with \textbf{bold} and \emph{emphasis}.
        \begin{equation}
        E = mc^2
        \end{equation}
        More text here.
        \end{document}
        """

        cleaned_text = processor.extract_text_from_tex(latex_text)
        assert "Test Paper" in cleaned_text
        assert "Test Author" in cleaned_text
        assert "This is some text" in cleaned_text
        assert "More text here" in cleaned_text
        # LaTeX commands should be removed or replaced
        assert "\\textbf" not in cleaned_text
        assert "\\documentclass" not in cleaned_text

    def test_main_tex_file_detection(self):
        """Test main TeX file detection."""
        processor = LaTeXProcessor()

        # Test with various file structures
        files_with_main = {
            "main.tex": b"\\documentclass{article}",
            "other.tex": b"\\input{main}",
            "figures/fig1.png": b"binary data",
        }

        main_file = processor.find_main_tex_file(files_with_main)
        assert main_file == "main.tex"

        # Test with paper.tex
        files_with_paper = {
            "paper.tex": b"\\documentclass{article}",
            "appendix.tex": b"\\section{Appendix}",
        }

        main_file = processor.find_main_tex_file(files_with_paper)
        assert main_file == "paper.tex"


class TestPDFProcessor:
    """Test the PDF processor functionality."""

    def test_processor_initialization(self):
        """Test PDF processor initialization."""
        processor = PDFProcessor()
        assert hasattr(processor, "extract_text_from_pdf")
        assert hasattr(processor, "get_pdf_metadata")

    def test_pdf_text_extraction_fallback(self):
        """Test PDF text extraction fallback when PyPDF2 unavailable."""
        processor = PDFProcessor()

        # Test with mock PDF content
        fake_pdf = b"%PDF-1.4 fake pdf content"

        # Should handle gracefully when PyPDF2 not available
        result = processor.extract_text_from_pdf(fake_pdf)
        assert isinstance(result, str)
        # Should either extract text or provide error message


class TestArxivPipeline:
    """Test the main ArXiv pipeline integration."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization with config."""
        config_dict = load_config()
        config = PipelineConfig.from_dict(config_dict)
        pipeline = ArxivPipeline(config)

        assert pipeline.config == config
        assert hasattr(pipeline, "downloader")
        assert hasattr(pipeline, "latex_processor")
        assert hasattr(pipeline, "pdf_processor")
        assert hasattr(pipeline, "process_paper")

    def test_pipeline_status(self):
        """Test pipeline status reporting."""
        config_dict = load_config()
        config = PipelineConfig.from_dict(config_dict)
        pipeline = ArxivPipeline(config)

        status = pipeline.get_pipeline_status()
        assert isinstance(status, dict)
        assert "config" in status
        assert "semaphores" in status
        assert "metrics" in status

        # Verify config values in status
        assert status["config"]["max_downloads"] == config.max_downloads


class TestModularIntegration:
    """Test integration between all modular components."""

    def test_import_integration(self):
        """Test that all modules can be imported together."""
        # This test validates that our modular refactoring preserved functionality
        try:
            from arxiv_mcp.tools import get_tools

            tools = get_tools()
            assert len(tools) > 0
        except ImportError:
            pytest.skip("Main module not available")

    def test_component_integration(self):
        """Test that components work together correctly."""
        # Test validator with pipeline
        validator = ArxivValidator()
        config_dict = load_config()
        config = PipelineConfig.from_dict(config_dict)

        # Test valid ArXiv ID
        arxiv_id = "2301.00001"
        assert validator.validate_arxiv_id(arxiv_id)

        # Test pipeline can be created with config
        pipeline = ArxivPipeline(config)
        assert pipeline is not None

    def test_error_propagation(self):
        """Test error propagation between modules."""
        # Test that custom exceptions can be raised and caught properly
        with pytest.raises(ArxivMCPError):
            raise DownloadError("Test error propagation")

        with pytest.raises(DownloadError):
            raise DownloadError("Specific download error")


class TestDependencyManagement:
    """Test handling of optional dependencies."""

    def test_optional_dependency_handling(self):
        """Test graceful handling when optional dependencies unavailable."""
        # Test PDF processor handles missing PyPDF2
        processor = PDFProcessor()

        # Should not raise exception during initialization
        assert processor is not None

        # Should handle missing dependency gracefully
        result = processor.extract_text_from_pdf(b"fake pdf")
        assert isinstance(result, str)

    @patch("arxiv_mcp.clients.aiohttp")
    def test_required_dependency_handling(self, mock_aiohttp):
        """Test handling of required dependencies."""
        # Test that downloader can be created even with mocked aiohttp
        downloader = AsyncArxivDownloader()
        assert downloader is not None


class TestConfigurationFlexibility:
    """Test configuration management flexibility."""

    def test_config_modification(self):
        """Test that configuration can be modified."""
        config_dict = load_config()
        original_downloads = config_dict["max_downloads"]

        # Modify config
        config_dict["max_downloads"] = 10
        config = PipelineConfig.from_dict(config_dict)

        assert config.max_downloads == 10
        assert config.max_downloads != original_downloads

    def test_config_validation(self):
        """Test configuration validation."""
        config_dict = load_config()

        # Test that all required fields are present
        required_fields = [
            "max_downloads",
            "max_extractions",
            "max_compilations",
            "requests_per_second",
            "burst_size",
            "download_timeout",
        ]

        for field in required_fields:
            assert field in config_dict

        # Test config creation
        config = PipelineConfig.from_dict(config_dict)
        assert isinstance(config, PipelineConfig)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
