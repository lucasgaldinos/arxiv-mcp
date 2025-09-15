#!/usr/bin/env python3
"""
Integration tests for pipeline.py with real coverage measurement.

Uses minimal mocking approach to enable proper coverage tracking across
run_in_executor boundaries. Based on proven pattern from unified_converter and batch_operations tests.
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from arxiv_mcp.core.pipeline import ArxivPipeline
from arxiv_mcp.core.config import PipelineConfig


@pytest.fixture
def temp_output_dir() -> Generator[str, None, None]:
    """Create temporary output directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def pipeline_config(temp_output_dir: str) -> PipelineConfig:
    """Create PipelineConfig for testing."""
    return PipelineConfig(
        output_directory=temp_output_dir,
        max_downloads=2,
        max_extractions=2,
        max_compilations=1,
        requests_per_second=1.0,
        download_timeout=30,
        compilation_timeout=120,
        enable_sandboxing=False,
        generate_tex_files=True,
        preserve_intermediates=False,
        burst_size=5,
        max_files_per_archive=50
    )


@pytest.fixture
def pipeline(pipeline_config: PipelineConfig) -> ArxivPipeline:
    """Create ArxivPipeline instance for testing."""
    return ArxivPipeline(pipeline_config)


# Mock data simulating real ArXiv content
MOCK_LATEX_SOURCE = b'''\\documentclass{article}
\\usepackage{amsmath}
\\title{Test Paper}
\\author{Test Author}
\\begin{document}
\\maketitle
\\section{Introduction}
This is a test paper with some mathematical content: $E = mc^2$.
\\section{Conclusion}
This concludes our test paper.
\\end{document}'''

MOCK_FILES_DICT = {
    "main.tex": MOCK_LATEX_SOURCE,
    "references.bib": b"@article{test2023, title={Test}, author={Author}, year={2023}}",
    "figure1.eps": b"mock eps content"
}

MOCK_PDF_CONTENT = b"%PDF-1.4 mock pdf content for testing"


class TestArxivPipelineIntegration:
    """Integration tests for ArxivPipeline with real code execution."""

    def test_constructor_and_basic_setup(self, pipeline_config: PipelineConfig) -> None:
        """Test ArxivPipeline initialization and basic setup."""
        pipeline = ArxivPipeline(pipeline_config)
        
        # Verify initialization
        assert pipeline.config == pipeline_config
        assert pipeline.downloader is not None
        assert pipeline.latex_processor is not None
        assert pipeline.pdf_processor is not None
        assert pipeline.document_processor is not None
        assert pipeline.validator is not None
        
        # Verify semaphores
        assert pipeline.download_semaphore._value == 2
        assert pipeline.extraction_semaphore._value == 2
        assert pipeline.compilation_semaphore._value == 1

    def test_get_pipeline_status(self, pipeline: ArxivPipeline) -> None:
        """Test pipeline status reporting."""
        status = pipeline.get_pipeline_status()
        
        # Verify status structure
        assert "config" in status
        assert "semaphores" in status
        assert "metrics" in status
        
        # Verify config values
        assert status["config"]["max_downloads"] == 2
        assert status["config"]["max_extractions"] == 2
        assert status["config"]["max_compilations"] == 1
        
        # Verify semaphore status
        assert status["semaphores"]["download_available"] == 2
        assert status["semaphores"]["extraction_available"] == 2
        assert status["semaphores"]["compilation_available"] == 1

    @pytest.mark.asyncio
    async def test_process_paper_basic_flow(self, pipeline: ArxivPipeline) -> None:
        """Test basic paper processing flow without PDF compilation."""
        arxiv_id = "2301.12345"
        
        # Mock the downloader with minimal mocking
        with patch.object(pipeline.downloader, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = MOCK_LATEX_SOURCE
            
            # Mock the latex processor methods that don't use run_in_executor
            with patch.object(pipeline.latex_processor, 'find_main_tex_file') as mock_find_main:
                mock_find_main.return_value = "main.tex"
                
                with patch.object(pipeline.latex_processor, 'extract_text_from_tex') as mock_extract_text:
                    mock_extract_text.return_value = "Extracted text content from LaTeX"
                    
                    # Mock the extract_archive method (this DOES use run_in_executor)
                    with patch.object(pipeline.latex_processor, 'extract_archive') as mock_extract_archive:
                        mock_extract_archive.return_value = MOCK_FILES_DICT
                        
                        # Execute the pipeline - this will exercise run_in_executor code paths
                        result = await pipeline.process_paper(arxiv_id, include_pdf=False)
                        
                        # Verify result structure
                        assert result["success"] is True
                        assert result["arxiv_id"] == arxiv_id
                        assert result["main_tex_file"] == "main.tex"
                        assert result["extracted_text"] == "Extracted text content from LaTeX"
                        assert result["file_count"] == 3
                        assert "pdf_compiled" not in result
                        
                        # Verify the run_in_executor path was called
                        mock_extract_archive.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_paper_with_pdf(self, pipeline: ArxivPipeline) -> None:
        """Test paper processing with PDF compilation (exercises both run_in_executor calls)."""
        arxiv_id = "2301.56789"
        
        # Mock network call
        with patch.object(pipeline.downloader, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = MOCK_LATEX_SOURCE
            
            # Mock latex processor methods
            with patch.object(pipeline.latex_processor, 'find_main_tex_file') as mock_find_main:
                mock_find_main.return_value = "main.tex"
                
                with patch.object(pipeline.latex_processor, 'extract_text_from_tex') as mock_extract_text:
                    mock_extract_text.return_value = "LaTeX text content"
                    
                    # Mock both run_in_executor methods
                    with patch.object(pipeline.latex_processor, 'extract_archive') as mock_extract_archive:
                        mock_extract_archive.return_value = MOCK_FILES_DICT
                        
                        with patch.object(pipeline.latex_processor, 'compile_latex') as mock_compile_latex:
                            mock_compile_latex.return_value = MOCK_PDF_CONTENT
                            
                            # Mock PDF processor methods
                            with patch.object(pipeline.pdf_processor, 'extract_text_from_pdf') as mock_pdf_text:
                                mock_pdf_text.return_value = "PDF extracted text"
                                
                                with patch.object(pipeline.pdf_processor, 'get_pdf_metadata') as mock_pdf_meta:
                                    mock_pdf_meta.return_value = {"title": "Test Paper", "author": "Test Author"}
                                    
                                    # Execute the pipeline with PDF compilation
                                    result = await pipeline.process_paper(arxiv_id, include_pdf=True)
                                    
                                    # Verify result structure
                                    assert result["success"] is True
                                    assert result["arxiv_id"] == arxiv_id
                                    assert result["pdf_compiled"] is True
                                    assert result["pdf_text"] == "PDF extracted text"
                                    assert result["pdf_metadata"]["title"] == "Test Paper"
                                    assert result["pdf_size"] == len(MOCK_PDF_CONTENT)
                                    
                                    # Verify both run_in_executor paths were called
                                    mock_extract_archive.assert_called_once()
                                    mock_compile_latex.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_paper_error_handling(self, pipeline: ArxivPipeline) -> None:
        """Test error handling in paper processing pipeline."""
        arxiv_id = "2301.99999"
        
        # Mock download failure
        with patch.object(pipeline.downloader, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Network error")
            
            # Execute the pipeline
            result = await pipeline.process_paper(arxiv_id, include_pdf=False)
            
            # Verify error handling
            assert result["success"] is False
            assert result["arxiv_id"] == arxiv_id
            assert "error" in result
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_process_multiple_papers(self, pipeline: ArxivPipeline) -> None:
        """Test concurrent processing of multiple papers."""
        arxiv_ids = ["2301.11111", "2301.22222", "2301.33333"]
        
        # Mock successful processing for all papers
        with patch.object(pipeline.downloader, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = MOCK_LATEX_SOURCE
            
            with patch.object(pipeline.latex_processor, 'extract_archive') as mock_extract_archive:
                mock_extract_archive.return_value = MOCK_FILES_DICT
                
                with patch.object(pipeline.latex_processor, 'find_main_tex_file') as mock_find_main:
                    mock_find_main.return_value = "main.tex"
                    
                    with patch.object(pipeline.latex_processor, 'extract_text_from_tex') as mock_extract_text:
                        mock_extract_text.return_value = "Extracted text"
                        
                        # Execute batch processing
                        results = await pipeline.process_multiple_papers(arxiv_ids, include_pdf=False)
                        
                        # Verify results
                        assert len(results) == 3
                        
                        for i, result in enumerate(results):
                            assert result["success"] is True
                            assert result["arxiv_id"] == arxiv_ids[i]
                            assert result["extracted_text"] == "Extracted text"
                        
                        # Verify concurrent calls were made
                        assert mock_download.call_count == 3
                        assert mock_extract_archive.call_count == 3

    @pytest.mark.asyncio
    async def test_process_document(self, pipeline: ArxivPipeline) -> None:
        """Test document processing functionality."""
        mock_content = b"Mock document content"
        filename = "test_document.docx"
        
        # Mock the document processor
        with patch.object(pipeline.document_processor, 'process_document') as mock_process:
            # Create a mock result object with all required attributes
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.format.value = "DOCX"
            mock_result.extracted_text = "Extracted document text"
            mock_result.error = None
            mock_result.warnings = []
            
            # Mock metadata
            mock_result.metadata.title = "Test Document"
            mock_result.metadata.author = "Test Author"
            mock_result.metadata.subject = "Test Subject"
            mock_result.metadata.creator = "Test Creator"
            mock_result.metadata.pages = 5
            mock_result.metadata.word_count = 100
            mock_result.metadata.language = "en"
            mock_result.metadata.created_date = "2023-01-01"
            mock_result.metadata.modified_date = "2023-01-02"
            
            mock_process.return_value = mock_result
            
            # Mock get_supported_formats
            mock_format_enum = MagicMock()
            mock_format_enum.value = "PDF"
            
            with patch.object(pipeline.document_processor, 'get_supported_formats') as mock_formats:
                mock_formats.return_value = [mock_format_enum]
                
                # Execute document processing
                result = await pipeline.process_document(mock_content, filename)
                
                # Verify result structure
                assert result["success"] is True
                assert result["format"] == "DOCX"
                assert result["extracted_text"] == "Extracted document text"
                assert result["metadata"]["title"] == "Test Document"
                assert result["metadata"]["pages"] == 5
                assert result["supported_formats"] == ["PDF"]
                
                # Verify processor was called correctly
                mock_process.assert_called_once_with(mock_content, filename)