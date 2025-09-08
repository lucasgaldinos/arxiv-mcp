"""
Unified download and convert tool for ArXiv papers.
Downloads papers and converts them to both LaTeX and Markdown formats with organized output.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..core.pipeline import ArxivPipeline
from ..core.config import PipelineConfig
from .file_saver import FileSaver
from .latex_to_markdown import LaTeXToMarkdownConverter
from ..utils.logging import structured_logger

logger = structured_logger()


class UnifiedDownloadConverter:
    """Unified tool for downloading and converting ArXiv papers to multiple formats."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig.from_dict({})
        self.pipeline = ArxivPipeline(self.config)
        self.file_saver = FileSaver(self.config.output_directory)
        self.markdown_converter = LaTeXToMarkdownConverter()
        logger.info(f"Unified download converter initialized with output: {self.config.output_directory}")
    
    async def download_and_convert(self, arxiv_id: str, 
                                 save_latex: bool = True,
                                 save_markdown: bool = True,
                                 include_pdf: bool = False) -> Dict[str, Any]:
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
                    "error": result.get("error", "Processing failed")
                }
            
            response = {
                "arxiv_id": arxiv_id,
                "success": True,
                "formats": [],
                "files": {},
                "metadata": {}
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
            
            # Save LaTeX files if requested
            if save_latex:
                latex_result = self.file_saver.save_latex_files(
                    arxiv_id, files, main_tex_file
                )
                response["formats"].append("latex")
                response["files"]["latex"] = latex_result
                logger.info(f"Saved LaTeX files for {arxiv_id}")
            
            # Convert and save Markdown if requested
            if save_markdown:
                # Get the main TeX content
                tex_content = files[main_tex_file].decode("utf-8", errors="ignore")
                
                # Convert to markdown with metadata extraction
                conversion_result = self.markdown_converter.convert_with_metadata(
                    tex_content, arxiv_id
                )
                
                if conversion_result["success"]:
                    # Save markdown file with YAML frontmatter
                    markdown_path = self.file_saver.save_markdown_file(
                        arxiv_id, 
                        conversion_result["markdown"],
                        conversion_result["metadata"]
                    )
                    
                    # Save metadata separately
                    metadata_path = self.file_saver.save_metadata(
                        arxiv_id, conversion_result["metadata"]
                    )
                    
                    response["formats"].append("markdown")
                    response["files"]["markdown"] = {
                        "file": markdown_path,
                        "metadata": metadata_path,
                        "conversion_method": conversion_result["conversion_method"]
                    }
                    response["metadata"] = conversion_result["metadata"]
                    
                    if conversion_result.get("warnings"):
                        response["warnings"] = conversion_result["warnings"]
                    
                    logger.info(f"Converted and saved markdown for {arxiv_id}")
                else:
                    logger.error(f"Markdown conversion failed for {arxiv_id}")
                    response["formats"].append("markdown_failed")
                    response["markdown_error"] = conversion_result.get("warnings", "Conversion failed")
            
            # Add processing summary
            response["summary"] = {
                "total_files": len(files),
                "main_tex_file": main_tex_file,
                "output_directory": str(self.file_saver.output_directory),
                "extracted_text_length": len(result.get("extracted_text", "")),
                "pdf_compiled": result.get("pdf_compiled", False)
            }
            
            logger.info(f"Completed unified processing for {arxiv_id}: {response['formats']}")
            return response
            
        except Exception as e:
            logger.error(f"Unified processing failed for {arxiv_id}: {str(e)}")
            return {
                "arxiv_id": arxiv_id,
                "success": False,
                "error": str(e)
            }
    
    async def batch_download_and_convert(self, arxiv_ids: List[str],
                                       save_latex: bool = True,
                                       save_markdown: bool = True,
                                       include_pdf: bool = False,
                                       max_concurrent: int = 3) -> Dict[str, Any]:
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
                failed.append({
                    "arxiv_id": arxiv_ids[i],
                    "error": str(result)
                })
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
            "output_directory": str(self.file_saver.output_directory)
        }
        
        logger.info(f"Batch processing completed: {len(successful)}/{len(arxiv_ids)} successful")
        return batch_result
    
    def get_output_structure(self) -> Dict[str, Any]:
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
                "metadata": str(self.file_saver.metadata_dir)
            },
            "saved_papers": saved_papers,
            "directory_exists": self.file_saver.output_directory.exists()
        }
        
        # Add directory contents if they exist
        if self.file_saver.latex_dir.exists():
            structure["latex_papers"] = [
                {
                    "arxiv_id": d.name,
                    "path": str(d),
                    "files": len(list(d.glob("*"))) if d.is_dir() else 0
                }
                for d in self.file_saver.latex_dir.iterdir() if d.is_dir()
            ]
        
        if self.file_saver.markdown_dir.exists():
            structure["markdown_papers"] = [
                {
                    "arxiv_id": d.name,
                    "path": str(d),
                    "markdown_file": str(d / f"{d.name}.md") if (d / f"{d.name}.md").exists() else None
                }
                for d in self.file_saver.markdown_dir.iterdir() if d.is_dir()
            ]
        
        return structure
    
    def cleanup_output(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old output files.
        
        Args:
            days_old: Number of days to keep files
            
        Returns:
            Cleanup statistics
        """
        return self.file_saver.cleanup_old_files(days_old)
    
    def validate_conversion_quality(self, arxiv_id: str) -> Dict[str, Any]:
        """Validate the quality of LaTeX to Markdown conversion.
        
        Args:
            arxiv_id: ArXiv paper ID to validate
            
        Returns:
            Quality assessment results
        """
        try:
            # Check if both formats exist
            latex_dir = self.file_saver.latex_dir / arxiv_id
            markdown_dir = self.file_saver.markdown_dir / arxiv_id
            
            if not latex_dir.exists():
                return {"error": f"LaTeX files not found for {arxiv_id}"}
            
            if not markdown_dir.exists():
                return {"error": f"Markdown files not found for {arxiv_id}"}
            
            # Get original LaTeX content
            manifest_path = latex_dir / "manifest.json"
            if not manifest_path.exists():
                return {"error": f"Manifest not found for {arxiv_id}"}
            
            import json
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            main_tex_file = manifest["main_tex_file"]
            latex_path = latex_dir / main_tex_file
            
            if not latex_path.exists():
                return {"error": f"Main LaTeX file not found: {main_tex_file}"}
            
            with open(latex_path, 'r', encoding='utf-8', errors='ignore') as f:
                latex_content = f.read()
            
            # Get converted markdown
            markdown_path = markdown_dir / f"{arxiv_id}.md"
            if not markdown_path.exists():
                return {"error": f"Markdown file not found for {arxiv_id}"}
            
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Basic quality metrics
            quality_metrics = {
                "arxiv_id": arxiv_id,
                "latex_length": len(latex_content),
                "markdown_length": len(markdown_content),
                "compression_ratio": len(markdown_content) / len(latex_content) if latex_content else 0,
                "has_yaml_frontmatter": markdown_content.startswith("---"),
                "sections_preserved": len(re.findall(r'^#+ ', markdown_content, re.MULTILINE)),
                "math_expressions": len(re.findall(r'\$.*?\$', markdown_content)),
                "conversion_date": manifest.get("saved_at")
            }
            
            # Check for common conversion issues
            issues = []
            if quality_metrics["compression_ratio"] < 0.1:
                issues.append("Very low compression ratio - possible conversion loss")
            if quality_metrics["sections_preserved"] == 0:
                issues.append("No section headers found in markdown")
            if "\\begin{" in markdown_content:
                issues.append("Unconverted LaTeX environments detected")
            if re.search(r'\\[a-zA-Z]+', markdown_content):
                issues.append("Unconverted LaTeX commands detected")
            
            quality_metrics["issues"] = issues
            quality_metrics["quality_score"] = max(0, 1.0 - (len(issues) * 0.2))
            
            return quality_metrics
            
        except Exception as e:
            return {"error": f"Quality validation failed: {str(e)}"}


# Convenience function for direct use
async def download_and_convert_paper(arxiv_id: str, 
                                   output_dir: str = "./output",
                                   save_latex: bool = True,
                                   save_markdown: bool = True) -> Dict[str, Any]:
    """Convenience function to download and convert a single paper.
    
    Args:
        arxiv_id: ArXiv paper ID
        output_dir: Output directory path
        save_latex: Whether to save LaTeX files
        save_markdown: Whether to convert and save markdown
        
    Returns:
        Processing results
    """
    config = PipelineConfig.from_dict({"output_directory": output_dir})
    converter = UnifiedDownloadConverter(config)
    
    return await converter.download_and_convert(
        arxiv_id, save_latex=save_latex, save_markdown=save_markdown
    )
