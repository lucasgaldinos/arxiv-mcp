"""
Unified download and convert tool for ArXiv papers.
Downloads papers and converts them to both LaTeX and Markdown formats with organized output.
"""

import asyncio
from pathlib import Path
import re
from typing import Any

from ..core.config import PipelineConfig
from ..core.pipeline import ArxivPipeline
from ..utils.logging import structured_logger
from .file_saver import FileSaver
from .latex_to_markdown import LaTeXToMarkdownConverter

logger = structured_logger()


class UnifiedDownloadConverter:
    """Unified tool for downloading and converting ArXiv papers to multiple formats."""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig.from_dict({})
        self.pipeline = ArxivPipeline(self.config)
        self.file_saver = FileSaver(self.config.output_directory)
        self.markdown_converter = LaTeXToMarkdownConverter()
        logger.info(
            f"Unified download converter initialized with output: {self.config.output_directory}"
        )

    async def download_and_convert(
        self,
        arxiv_id: str,
        save_latex: bool = True,
        save_markdown: bool = True,
        include_pdf: bool = False,
    ) -> dict[str, Any]:
        """Download and convert an ArXiv paper to multiple formats.

        Args:
            arxiv_id: ArXiv paper ID
            save_latex: Whether to save LaTeX files
            save_markdown: Whether to convert and save markdown
            include_pdf: Whether to include PDF compilation

        Returns:
            Dictionary with processing results and file locations
        """
        logger.info(f"Starting unified download and convert for {arxiv_id}")

        try:
            # Download and process the paper
            result = await self.pipeline.process_paper(arxiv_id, include_pdf=include_pdf)

            if not result.get("success"):
                return {
                    "arxiv_id": arxiv_id,
                    "success": False,
                    "error": result.get("error", "Processing failed"),
                }

            response = {
                "arxiv_id": arxiv_id,
                "success": True,
                "formats": [],
                "files": {},
                "metadata": {},
            }

            # Get the raw files for saving
            source_content = await self.pipeline.downloader.download(
                arxiv_id, timeout=self.config.download_timeout
            )
            files = await asyncio.get_event_loop().run_in_executor(
                None,
                self.pipeline.latex_processor.extract_archive,
                source_content,
                self.config.max_files_per_archive,
            )

            main_tex_file = result["main_tex_file"]

            # Pre-extract metadata for directory naming
            paper_metadata = None
            if save_markdown or save_latex:
                # Get the main TeX content for metadata extraction
                tex_content = files[main_tex_file].decode("utf-8", errors="ignore")
                conversion_result = self.markdown_converter.convert_with_metadata(
                    tex_content, arxiv_id
                )
                if conversion_result["success"]:
                    paper_metadata = conversion_result["metadata"]

            # Save LaTeX files if requested
            if save_latex:
                latex_result = self.file_saver.save_latex_files(
                    arxiv_id, files, main_tex_file, paper_metadata
                )
                response["formats"].append("latex")
                response["files"]["latex"] = latex_result
                logger.info(f"Saved LaTeX files for {arxiv_id}")

            # Convert and save Markdown if requested
            if save_markdown:
                # Use pre-extracted metadata or extract fresh if not available
                if paper_metadata is None:
                    # Get the main TeX content
                    tex_content = files[main_tex_file].decode("utf-8", errors="ignore")

                    # Convert to markdown with metadata extraction
                    conversion_result = self.markdown_converter.convert_with_metadata(
                        tex_content, arxiv_id
                    )
                else:
                    # Use the already extracted metadata and conversion
                    conversion_result = {
                        "success": True,
                        "metadata": paper_metadata,
                        "markdown": self.markdown_converter.convert(tex_content, paper_metadata),
                        "conversion_method": "pandoc_with_metadata",
                    }

                if conversion_result["success"]:
                    # Save markdown file with YAML frontmatter
                    markdown_path = self.file_saver.save_markdown_file(
                        arxiv_id,
                        conversion_result["markdown"],
                        conversion_result["metadata"],
                    )

                    # Save metadata separately
                    metadata_path = self.file_saver.save_metadata(
                        arxiv_id, conversion_result["metadata"]
                    )

                    response["formats"].append("markdown")
                    response["files"]["markdown"] = {
                        "file": markdown_path,
                        "metadata": metadata_path,
                        "conversion_method": conversion_result["conversion_method"],
                    }
                    response["metadata"] = conversion_result["metadata"]

                    if conversion_result.get("warnings"):
                        response["warnings"] = conversion_result["warnings"]

                    logger.info(f"Converted and saved markdown for {arxiv_id}")
                else:
                    logger.error(f"Markdown conversion failed for {arxiv_id}")
                    response["formats"].append("markdown_failed")
                    response["markdown_error"] = conversion_result.get(
                        "warnings", "Conversion failed"
                    )

            # Save PDF if requested and available
            if include_pdf and result.get("pdf_content"):
                try:
                    # Use metadata from markdown conversion if available
                    pdf_metadata = response.get("metadata", {"arxiv_id": arxiv_id})
                    pdf_path = self.file_saver.save_pdf_file(
                        arxiv_id, result["pdf_content"], pdf_metadata
                    )
                    response["formats"].append("pdf")
                    response["files"]["pdf"] = {
                        "file": pdf_path,
                        "compilation_method": "latex",
                    }
                    logger.info(f"Saved PDF file for {arxiv_id}")
                except Exception as e:
                    logger.error(f"PDF saving failed for {arxiv_id}: {str(e)}")
                    response["formats"].append("pdf_failed")
                    response["pdf_error"] = str(e)

            # Add processing summary
            response["summary"] = {
                "total_files": len(files),
                "main_tex_file": main_tex_file,
                "output_directory": str(self.file_saver.output_directory),
                "extracted_text_length": len(result.get("extracted_text", "")),
                "pdf_compiled": result.get("pdf_compiled", False),
            }

            logger.info(f"Completed unified processing for {arxiv_id}: {response['formats']}")
            return response

        except Exception as e:
            logger.exception(f"Unified processing failed for {arxiv_id}: {str(e)}")
            return {"arxiv_id": arxiv_id, "success": False, "error": str(e)}

    async def batch_download_and_convert(
        self,
        arxiv_ids: list[str],
        save_latex: bool = True,
        save_markdown: bool = True,
        include_pdf: bool = False,
        max_concurrent: int = 3,
    ) -> dict[str, Any]:
        """Batch download and convert multiple ArXiv papers.

        Args:
            arxiv_ids: List of ArXiv paper IDs
            save_latex: Whether to save LaTeX files
            save_markdown: Whether to convert and save markdown
            include_pdf: Whether to include PDF compilation
            max_concurrent: Maximum concurrent downloads

        Returns:
            Dictionary with batch processing results
        """
        logger.info(f"Starting batch processing for {len(arxiv_ids)} papers")

        # Create semaphore for concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(arxiv_id: str):
            async with semaphore:
                return await self.download_and_convert(
                    arxiv_id, save_latex, save_markdown, include_pdf
                )

        # Process all papers concurrently
        tasks = [process_with_semaphore(arxiv_id) for arxiv_id in arxiv_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile batch results
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({"arxiv_id": arxiv_ids[i], "error": str(result)})
            elif result.get("success"):
                successful.append(result)
            else:
                failed.append(result)

        batch_result = {
            "total_papers": len(arxiv_ids),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(arxiv_ids) if arxiv_ids else 0,
            "results": successful,
            "failures": failed,
            "output_directory": str(self.file_saver.output_directory),
        }

        logger.info(f"Batch processing completed: {len(successful)}/{len(arxiv_ids)} successful")
        return batch_result

    def get_output_structure(self) -> dict[str, Any]:
        """Get information about the output directory structure.

        Returns:
            Dictionary describing the output structure
        """
        saved_papers = self.file_saver.get_saved_papers()

        structure = {
            "output_directory": str(self.file_saver.output_directory),
            "subdirectories": {
                "latex": str(self.file_saver.latex_dir),
                "markdown": str(self.file_saver.markdown_dir),
                "metadata": str(self.file_saver.metadata_dir),
                "pdf": str(self.file_saver.pdf_dir),
            },
            "saved_papers": saved_papers,
            "directory_exists": self.file_saver.output_directory.exists(),
        }

        # Add directory contents if they exist
        if self.file_saver.latex_dir.exists():
            structure["latex_papers"] = [
                {
                    "arxiv_id": d.name,
                    "path": str(d),
                    "files": len(list(d.glob("*"))) if d.is_dir() else 0,
                }
                for d in self.file_saver.latex_dir.iterdir()
                if d.is_dir()
            ]

        if self.file_saver.markdown_dir.exists():
            structure["markdown_papers"] = [
                {
                    "arxiv_id": d.name,
                    "path": str(d),
                    "markdown_file": (
                        str(d / f"{d.name}.md") if (d / f"{d.name}.md").exists() else None
                    ),
                }
                for d in self.file_saver.markdown_dir.iterdir()
                if d.is_dir()
            ]

        if self.file_saver.pdf_dir.exists():
            structure["pdf_papers"] = [
                {
                    "arxiv_id": d.name,
                    "path": str(d),
                    "pdf_file": (
                        str(d / f"{d.name}.pdf") if (d / f"{d.name}.pdf").exists() else None
                    ),
                }
                for d in self.file_saver.pdf_dir.iterdir()
                if d.is_dir()
            ]

        return structure

    def cleanup_output(self, days_old: int = 30) -> dict[str, Any]:
        """Clean up old output files.

        Args:
            days_old: Number of days to keep files

        Returns:
            Cleanup statistics
        """
        return self.file_saver.cleanup_old_files(days_old)

    def validate_conversion_quality(
        self, arxiv_id: str, format_type: str = "single"
    ) -> dict[str, Any]:
        """Validate the quality of document processing with independent format support.

        Args:
            arxiv_id: ArXiv paper ID to validate
            format_type: Validation mode - "single" (auto-detect), "latex_only", "markdown_only", or "both" (legacy)

        Returns:
            Quality assessment results with independent format metrics
        """
        try:
            # Auto-detect available formats for single mode
            latex_dir = self.file_saver.latex_dir / arxiv_id
            markdown_dir = self.file_saver.markdown_dir / arxiv_id

            latex_available = latex_dir.exists()
            markdown_available = markdown_dir.exists()

            # Determine actual validation mode
            if format_type == "single":
                if markdown_available:
                    actual_mode = "markdown_only"
                elif latex_available:
                    actual_mode = "latex_only"
                else:
                    return {"error": f"No processed files found for {arxiv_id}"}
            else:
                actual_mode = format_type

            # Validate format availability
            if actual_mode in ["both", "latex_only"] and not latex_available:
                return {"error": f"LaTeX files not found for {arxiv_id}"}
            if actual_mode in ["both", "markdown_only"] and not markdown_available:
                return {"error": f"Markdown files not found for {arxiv_id}"}

            # Initialize quality assessment
            quality_metrics = {
                "arxiv_id": arxiv_id,
                "validation_mode": actual_mode,
                "detected_formats": {"latex": latex_available, "markdown": markdown_available},
                "timestamp": self._get_current_timestamp(),
                "independent_quality_scores": {},
            }

            # Independent LaTeX validation
            if actual_mode in ["both", "latex_only"]:
                latex_metrics = self._validate_latex_quality(latex_dir, arxiv_id)
                quality_metrics["independent_quality_scores"]["latex"] = latex_metrics
                quality_metrics.update({f"latex_{k}": v for k, v in latex_metrics.items()})

            # Independent Markdown validation
            if actual_mode in ["both", "markdown_only"]:
                markdown_metrics = self._validate_markdown_quality(markdown_dir, arxiv_id)
                quality_metrics["independent_quality_scores"]["markdown"] = markdown_metrics
                quality_metrics.update({f"markdown_{k}": v for k, v in markdown_metrics.items()})

            # Calculate overall quality score (target: 90%+)
            scores = []
            if "latex" in quality_metrics["independent_quality_scores"]:
                scores.append(
                    quality_metrics["independent_quality_scores"]["latex"]["quality_score"]
                )
            if "markdown" in quality_metrics["independent_quality_scores"]:
                scores.append(
                    quality_metrics["independent_quality_scores"]["markdown"]["quality_score"]
                )

            quality_metrics["overall_quality_score"] = sum(scores) / len(scores) if scores else 0.0
            quality_metrics["meets_target"] = quality_metrics["overall_quality_score"] >= 0.90

            # Legacy compression ratio if both formats available
            if actual_mode == "both":
                latex_len = quality_metrics.get("latex_content_length", 0)
                markdown_len = quality_metrics.get("markdown_content_length", 0)
                if latex_len > 0:
                    quality_metrics["compression_ratio"] = markdown_len / latex_len

            return quality_metrics

        except Exception as e:
            return {"error": f"Quality validation failed: {str(e)}"}

    def _validate_latex_quality(self, latex_dir: Path, arxiv_id: str) -> dict[str, Any]:
        """Independent LaTeX quality validation."""
        try:
            # Load manifest and content
            manifest_path = latex_dir / "manifest.json"
            if not manifest_path.exists():
                return {"error": "Manifest not found", "quality_score": 0.0}

            import json

            with open(manifest_path) as f:
                manifest = json.load(f)

            main_tex_file = manifest["main_tex_file"]
            latex_path = latex_dir / main_tex_file

            if not latex_path.exists():
                return {
                    "error": f"Main LaTeX file not found: {main_tex_file}",
                    "quality_score": 0.0,
                }

            with open(latex_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # LaTeX-specific quality metrics
            metrics = {
                "content_length": len(content),
                "has_document_structure": bool(
                    re.search(r"\\documentclass|\\begin{document}", content)
                ),
                "section_count": len(re.findall(r"\\(sub)*section\{", content)),
                "math_environments": len(re.findall(r"\\begin{(equation|align|math)", content)),
                "citation_count": len(re.findall(r"\\cite{", content)),
                "figure_count": len(re.findall(r"\\begin{figure}", content)),
                "table_count": len(re.findall(r"\\begin{table}", content)),
                "is_main_content": len(content) >= 1000,
                "saved_at": manifest.get("saved_at"),
                "issues": [],
            }

            # LaTeX quality issues detection
            if not metrics["has_document_structure"]:
                metrics["issues"].append("Missing document structure")
            if metrics["content_length"] < 1000:
                metrics["issues"].append("Content appears unusually short")
            if metrics["section_count"] == 0:
                metrics["issues"].append("No sections found")

            # Calculate LaTeX quality score (0.0 - 1.0)
            score = 0.0
            if metrics["has_document_structure"]:
                score += 0.3
            if metrics["is_main_content"]:
                score += 0.2
            if metrics["section_count"] > 0:
                score += 0.2
            if metrics["math_environments"] > 0:
                score += 0.1
            if metrics["citation_count"] > 0:
                score += 0.1
            if len(metrics["issues"]) == 0:
                score += 0.1

            metrics["quality_score"] = min(score, 1.0)

            return metrics

        except Exception as e:
            return {"error": f"LaTeX validation failed: {str(e)}", "quality_score": 0.0}

    def _validate_markdown_quality(self, markdown_dir: Path, arxiv_id: str) -> dict[str, Any]:
        """Independent Markdown quality validation."""
        try:
            markdown_path = markdown_dir / f"{arxiv_id}.md"
            if not markdown_path.exists():
                return {"error": "Markdown file not found", "quality_score": 0.0}

            with open(markdown_path, encoding="utf-8") as f:
                content = f.read()

            # Markdown-specific quality metrics
            metrics = {
                "content_length": len(content),
                "has_yaml_frontmatter": content.startswith("---"),
                "section_count": len(re.findall(r"^#+\s", content, re.MULTILINE)),
                "math_expressions": len(re.findall(r"\$.*?\$", content)),
                "code_blocks": len(re.findall(r"```", content)) // 2,
                "links_count": len(re.findall(r"\[.*?\]\(.*?\)", content)),
                "images_count": len(re.findall(r"!\[.*?\]\(.*?\)", content)),
                "tables_count": len(re.findall(r"^\|.*\|", content, re.MULTILINE)),
                "conversion_artifacts": 0,
                "issues": [],
            }

            # Conversion quality analysis
            artifacts = [
                (r"\\begin{", "Unconverted LaTeX environments"),
                (r"\\[a-zA-Z]+(?![a-zA-Z])", "Unconverted LaTeX commands"),
                (r"&[a-zA-Z]+;", "HTML entities"),
                (r"<[^>]+>", "Unconverted HTML tags"),
            ]

            for pattern, issue_desc in artifacts:
                matches = re.findall(pattern, content)
                if matches:
                    metrics["conversion_artifacts"] += len(matches)
                    metrics["issues"].append(f"{issue_desc}: {len(matches)} found")

            # Markdown quality issues detection
            if metrics["content_length"] < 500:
                metrics["issues"].append("Content appears unusually short")
            if metrics["section_count"] == 0:
                metrics["issues"].append("No section headers found")
            if metrics["conversion_artifacts"] > 10:
                metrics["issues"].append("High number of conversion artifacts")

            # Calculate Markdown quality score (0.0 - 1.0)
            score = 0.0
            if metrics["content_length"] >= 500:
                score += 0.2
            if metrics["section_count"] > 0:
                score += 0.3
            if metrics["has_yaml_frontmatter"]:
                score += 0.1
            if metrics["math_expressions"] > 0:
                score += 0.1
            if metrics["conversion_artifacts"] == 0:
                score += 0.2
            if len(metrics["issues"]) == 0:
                score += 0.1

            metrics["quality_score"] = min(score, 1.0)

            return metrics

        except Exception as e:
            return {"error": f"Markdown validation failed: {str(e)}", "quality_score": 0.0}

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for validation."""
        from datetime import datetime

        return datetime.now().isoformat()


# Convenience function for direct use
async def download_and_convert_paper(
    arxiv_id: str,
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
) -> dict[str, Any]:
    """Convenience function to download and convert a single paper.

    Args:
        arxiv_id: ArXiv paper ID
        output_dir: Output directory path
        save_latex: Whether to save LaTeX files
        save_markdown: Whether to convert and save markdown
        include_pdf: Whether to include PDF compilation

    Returns:
        Processing results
    """
    import os
    
    # Resolve output directory relative to current working directory (client's directory)
    if not os.path.isabs(output_dir):
        cwd = os.getcwd()
        resolved_output_dir = os.path.join(cwd, output_dir)
    else:
        resolved_output_dir = output_dir

    config = PipelineConfig.from_dict({"output_directory": resolved_output_dir})
    converter = UnifiedDownloadConverter(config)

    return await converter.download_and_convert(
        arxiv_id, save_latex=save_latex, save_markdown=save_markdown, include_pdf=include_pdf
    )
