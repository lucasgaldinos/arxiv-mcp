"""
Core pipeline orchestration for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.
"""

import asyncio
from typing import Any

from ..clients import AsyncArxivDownloader
from ..exceptions import ArxivError, ProcessingError
from ..processors import DocumentProcessor, LaTeXProcessor, PDFProcessor
from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector
from ..utils.validation import ArxivValidator
from .config import PipelineConfig


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

    async def process_paper(self, arxiv_id: str, include_pdf: bool = True, max_retries: int = 3) -> dict[str, Any]:
        """Process a single ArXiv paper through the complete pipeline with robust error recovery."""
        self.logger.info(f"Starting pipeline processing for {arxiv_id}")

        for attempt in range(max_retries + 1):
            try:
                # Validate ArXiv ID
                if not self.validator.validate_arxiv_id(arxiv_id):
                    raise ArxivError(f"Invalid ArXiv ID format: {arxiv_id}")

                # Download source with retry logic
                source_content = None
                download_attempts = min(3, max_retries)
                
                for download_attempt in range(download_attempts):
                    try:
                        async with self.download_semaphore:
                            source_content = await self.downloader.download(
                                arxiv_id, timeout=self.config.download_timeout
                            )
                        break  # Success, exit download retry loop
                    except Exception as download_error:
                        if download_attempt < download_attempts - 1:
                            wait_time = 2 ** download_attempt  # Exponential backoff
                            self.logger.warning(
                                f"Download attempt {download_attempt + 1} failed for {arxiv_id}, "
                                f"retrying in {wait_time}s: {download_error}"
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            raise  # Re-raise on final attempt

                if source_content is None:
                    raise ArxivError(f"Failed to download content for {arxiv_id}")

                # Extract files with enhanced error handling
                files = None
                extraction_attempts = min(2, max_retries)
                
                for extraction_attempt in range(extraction_attempts):
                    try:
                        async with self.extraction_semaphore:
                            files = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.latex_processor.extract_archive,
                                source_content,
                                self.config.max_files_per_archive,
                            )
                        break  # Success, exit extraction retry loop
                    except Exception as extraction_error:
                        if extraction_attempt < extraction_attempts - 1:
                            self.logger.warning(
                                f"Extraction attempt {extraction_attempt + 1} failed for {arxiv_id}, "
                                f"retrying: {extraction_error}"
                            )
                            # Try with different extraction method or parameters
                            await asyncio.sleep(1)
                        else:
                            # Try fallback extraction methods
                            try:
                                self.logger.info(f"Attempting fallback extraction for {arxiv_id}")
                                files = await self._fallback_extraction(source_content, arxiv_id)
                                if files:
                                    break
                            except Exception:
                                pass
                            raise  # Re-raise on final attempt

                if not files:
                    raise ProcessingError(f"No files extracted from {arxiv_id}")

                # Find main TeX file with fallback strategies
                main_tex_file = self.latex_processor.find_main_tex_file(files)
                if not main_tex_file:
                    # Try alternative main file detection strategies
                    main_tex_file = self._find_main_tex_fallback(files, arxiv_id)
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
                    "attempts": attempt + 1,
                }

                # Optionally compile to PDF with enhanced error handling
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
                                "pdf_content": pdf_content,
                                "pdf_text": pdf_text,
                                "pdf_metadata": pdf_metadata,
                                "pdf_size": len(pdf_content),
                            }
                        )

                    except Exception as e:
                        self.logger.warning(f"PDF compilation failed for {arxiv_id}: {str(e)}")
                        result.update({"pdf_compiled": False, "pdf_error": str(e)})

                self.metrics.increment_counter("pipeline_success", {"arxiv_id": arxiv_id})
                self.logger.info(
                    f"Pipeline processing completed successfully for {arxiv_id} "
                    f"(attempt {attempt + 1})"
                )
                return result

            except (ArxivError, ProcessingError) as e:
                # These are likely permanent errors, don't retry
                self.logger.error(f"Permanent error for {arxiv_id}: {str(e)}")
                self.metrics.increment_counter("pipeline_error", {"arxiv_id": arxiv_id, "type": "permanent"})
                return {"arxiv_id": arxiv_id, "success": False, "error": str(e), "error_type": "permanent"}
                
            except Exception as e:
                # Potentially transient errors, consider retry
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {arxiv_id}, "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.logger.exception(f"All {max_retries + 1} attempts failed for {arxiv_id}")
                    self.metrics.increment_counter("pipeline_error", {"arxiv_id": arxiv_id, "type": "max_retries"})
                    return {
                        "arxiv_id": arxiv_id,
                        "success": False,
                        "error": str(e),
                        "error_type": "max_retries_exceeded",
                        "attempts": max_retries + 1,
                    }

        # Should never reach here
        return {"arxiv_id": arxiv_id, "success": False, "error": "Unknown error"}

    async def _fallback_extraction(self, content, arxiv_id: str) -> dict[str, bytes]:
        """Attempt fallback extraction methods for problematic archives."""
        self.logger.info(f"Attempting fallback extraction methods for {arxiv_id}")
        
        # Try the ArxivLatexFetcher extraction method as fallback
        from ..utils.latex_fetcher import ArxivLatexFetcher
        
        try:
            fetcher = ArxivLatexFetcher()
            content_bytes = content.read() if hasattr(content, 'read') else content.getvalue()
            files = await fetcher._extract_archive(content_bytes, arxiv_id)
            if files:
                self.logger.info(f"Fallback extraction successful for {arxiv_id}")
                return files
        except Exception as e:
            self.logger.warning(f"Fallback extraction also failed for {arxiv_id}: {e}")
            
        return {}

    def _find_main_tex_fallback(self, files: dict[str, bytes], arxiv_id: str) -> str | None:
        """Fallback strategies for finding main TeX file."""
        self.logger.info(f"Attempting fallback main TeX file detection for {arxiv_id}")
        
        # Strategy 1: Look for files with \documentclass but be more permissive
        tex_files = [name for name in files if name.endswith(".tex")]
        
        for tex_file in tex_files:
            try:
                content = files[tex_file].decode("utf-8", errors="ignore")
                # Look for any document structure indicators
                if any(indicator in content for indicator in [
                    r"\documentclass", r"\begin{document}", r"\maketitle",
                    r"\section", r"\chapter", r"\abstract"
                ]):
                    self.logger.info(f"Found main file using fallback strategy: {tex_file}")
                    return tex_file
            except Exception:
                continue
                
        # Strategy 2: If only one TeX file, use it
        if len(tex_files) == 1:
            self.logger.info(f"Using single TeX file as main: {tex_files[0]}")
            return tex_files[0]
            
        # Strategy 3: Use largest TeX file
        if tex_files:
            largest_file = max(tex_files, key=lambda f: len(files[f]))
            self.logger.info(f"Using largest TeX file as main: {largest_file}")
            return largest_file
            
        return None

    async def process_multiple_papers(
        self, arxiv_ids: list[str], include_pdf: bool = True
    ) -> list[dict[str, Any]]:
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

    def get_pipeline_status(self) -> dict[str, Any]:
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

    async def process_document(self, content: bytes, filename: str = None) -> dict[str, Any]:
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
            self.logger.exception(f"Document processing failed: {str(e)}")
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
