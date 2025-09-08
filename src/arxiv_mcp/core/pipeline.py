"""
Core pipeline orchestration for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.
"""

import asyncio
from typing import Dict, Any, List

from .config import PipelineConfig
from ..clients import AsyncArxivDownloader
from ..processors import LaTeXProcessor, PDFProcessor, DocumentProcessor
from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector
from ..utils.validation import ArxivValidator
from ..exceptions import ArxivError, ProcessingError


class ArxivPipeline:
    """Enhanced ArXiv processing pipeline with async support and comprehensive error handling."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.downloader = AsyncArxivDownloader(
            requests_per_second=config.requests_per_second, burst_size=config.burst_size
        )
        self.latex_processor = LaTeXProcessor(
            compilation_timeout=config.compilation_timeout,
            enable_sandboxing=config.enable_sandboxing,
            generate_tex_files=config.generate_tex_files,
            output_directory=config.output_directory,
            preserve_intermediates=config.preserve_intermediates,
        )
        self.pdf_processor = PDFProcessor()
        self.document_processor = DocumentProcessor()  # NEW: Multi-format document processor
        self.validator = ArxivValidator()
        self.logger = structured_logger()
        self.metrics = MetricsCollector()

        # Semaphores for resource management
        self.download_semaphore = asyncio.Semaphore(config.max_downloads)
        self.extraction_semaphore = asyncio.Semaphore(config.max_extractions)
        self.compilation_semaphore = asyncio.Semaphore(config.max_compilations)

    async def process_paper(self, arxiv_id: str, include_pdf: bool = True) -> Dict[str, Any]:
        """Process a single ArXiv paper through the complete pipeline."""
        self.logger.info(f"Starting pipeline processing for {arxiv_id}")

        try:
            # Validate ArXiv ID
            if not self.validator.validate_arxiv_id(arxiv_id):
                raise ArxivError(f"Invalid ArXiv ID format: {arxiv_id}")

            # Download source
            async with self.download_semaphore:
                source_content = await self.downloader.download(
                    arxiv_id, timeout=self.config.download_timeout
                )

            # Extract files
            async with self.extraction_semaphore:
                files = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.latex_processor.extract_archive,
                    source_content,
                    self.config.max_files_per_archive,
                )

            # Find main TeX file
            main_tex_file = self.latex_processor.find_main_tex_file(files)
            if not main_tex_file:
                raise ProcessingError(f"No main TeX file found in {arxiv_id}")

            # Extract text from LaTeX
            tex_content = files[main_tex_file].decode("utf-8", errors="ignore")
            extracted_text = self.latex_processor.extract_text_from_tex(tex_content)

            result = {
                "arxiv_id": arxiv_id,
                "main_tex_file": main_tex_file,
                "extracted_text": extracted_text,
                "file_count": len(files),
                "success": True,
            }

            # Optionally compile to PDF
            if include_pdf:
                try:
                    async with self.compilation_semaphore:
                        pdf_content = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.latex_processor.compile_latex,
                            files,
                            main_tex_file,
                        )

                    # Extract PDF text and metadata
                    pdf_text = self.pdf_processor.extract_text_from_pdf(pdf_content)
                    pdf_metadata = self.pdf_processor.get_pdf_metadata(pdf_content)

                    result.update(
                        {
                            "pdf_compiled": True,
                            "pdf_text": pdf_text,
                            "pdf_metadata": pdf_metadata,
                            "pdf_size": len(pdf_content),
                        }
                    )

                except Exception as e:
                    self.logger.warning(f"PDF compilation failed for {arxiv_id}: {str(e)}")
                    result.update({"pdf_compiled": False, "pdf_error": str(e)})

            self.metrics.increment_counter("pipeline_success", {"arxiv_id": arxiv_id})
            self.logger.info(f"Pipeline processing completed successfully for {arxiv_id}")
            return result

        except Exception as e:
            self.metrics.increment_counter("pipeline_error", {"arxiv_id": arxiv_id})
            self.logger.error(f"Pipeline processing failed for {arxiv_id}: {str(e)}")
            return {"arxiv_id": arxiv_id, "success": False, "error": str(e)}

    async def process_multiple_papers(
        self, arxiv_ids: List[str], include_pdf: bool = True
    ) -> List[Dict[str, Any]]:
        """Process multiple ArXiv papers concurrently."""
        self.logger.info(f"Starting batch processing for {len(arxiv_ids)} papers")

        # Create tasks for concurrent processing
        tasks = [self.process_paper(arxiv_id, include_pdf) for arxiv_id in arxiv_ids]

        # Execute tasks with proper error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"arxiv_id": arxiv_ids[i], "success": False, "error": str(result)}
                )
            else:
                processed_results.append(result)

        self.logger.info(f"Batch processing completed for {len(arxiv_ids)} papers")
        return processed_results

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics."""
        return {
            "config": {
                "max_downloads": self.config.max_downloads,
                "max_extractions": self.config.max_extractions,
                "max_compilations": self.config.max_compilations,
                "requests_per_second": self.config.requests_per_second,
            },
            "semaphores": {
                "download_available": self.download_semaphore._value,
                "extraction_available": self.extraction_semaphore._value,
                "compilation_available": self.compilation_semaphore._value,
            },
            "metrics": self.metrics.get_all_metrics(),
        }

    async def process_document(self, content: bytes, filename: str = None) -> Dict[str, Any]:
        """Process a document in various formats (ODT, RTF, DOCX, etc.)."""
        self.logger.info(f"Starting document processing for {filename or 'unnamed file'}")

        try:
            # Use the document processor
            result = self.document_processor.process_document(content, filename)

            return {
                "success": result.success,
                "format": result.format.value,
                "extracted_text": result.extracted_text,
                "metadata": {
                    "title": result.metadata.title,
                    "author": result.metadata.author,
                    "subject": result.metadata.subject,
                    "creator": result.metadata.creator,
                    "pages": result.metadata.pages,
                    "word_count": result.metadata.word_count,
                    "language": result.metadata.language,
                    "created_date": result.metadata.created_date,
                    "modified_date": result.metadata.modified_date,
                },
                "error": result.error,
                "warnings": result.warnings or [],
                "supported_formats": [
                    fmt.value for fmt in self.document_processor.get_supported_formats()
                ],
            }

        except Exception as e:
            self.logger.error(f"Document processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "metadata": {},
                "warnings": [],
                "supported_formats": [
                    fmt.value for fmt in self.document_processor.get_supported_formats()
                ],
            }
