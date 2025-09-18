"""
File saving utilities for ArXiv papers.
Handles saving LaTeX files, markdown files, and metadata to organized directory structure.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ..utils.logging import structured_logger
from .filename_generator import FilenameGenerator

logger = structured_logger()


class FileSaver:
    """Handles saving ArXiv papers in paper-name-centric directory structure."""

    def __init__(self, output_directory: str = "./output", use_intelligent_naming: bool = True):
        self.output_directory = Path(output_directory)
        self.use_intelligent_naming = use_intelligent_naming
        self.filename_generator = FilenameGenerator() if use_intelligent_naming else None

        # Create base output directory
        self.output_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory initialized: {self.output_directory}")

    def _get_paper_directory_name(self, arxiv_id: str, metadata: dict[str, Any] = None) -> str:
        """Generate paper directory name using intelligent naming or arxiv_id fallback.
        
        Args:
            arxiv_id: ArXiv paper ID
            metadata: Optional metadata for intelligent naming
            
        Returns:
            Directory name for the paper
        """
        if self.use_intelligent_naming and self.filename_generator and metadata:
            # Generate clean paper name from title and authors
            paper_name = self.filename_generator.generate_paper_directory_name(arxiv_id, metadata)
            logger.info(f"Generated paper directory name: {paper_name} for {arxiv_id}")
            return paper_name
        else:
            # Fallback to arxiv_id
            return arxiv_id
    
    def _ensure_paper_directory(self, paper_name: str) -> Path:
        """Create paper directory with subdirectories for different formats.
        
        Args:
            paper_name: Name of the paper directory
            
        Returns:
            Path to the paper directory
        """
        paper_dir = self.output_directory / paper_name
        
        # Create subdirectories for different formats
        for subdir in ["latex", "markdown", "pdf", "metadata"]:
            (paper_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        return paper_dir

    def save_latex_files(
        self, arxiv_id: str, files: dict[str, bytes], main_tex_file: str, metadata: dict[str, Any] = None
    ) -> dict[str, str]:
        """Save LaTeX files to paper-centric directory structure.

        Args:
            arxiv_id: ArXiv paper ID
            files: Dictionary of filename -> file content
            main_tex_file: Name of the main .tex file
            metadata: Optional metadata for intelligent directory naming

        Returns:
            Dictionary with saved file paths
        """
        # Get paper directory name
        paper_name = self._get_paper_directory_name(arxiv_id, metadata)
        paper_dir = self._ensure_paper_directory(paper_name)
        latex_dir = paper_dir / "latex"

        saved_files = {}

        for filename, content in files.items():
            file_path = latex_dir / filename
            
            # Ensure parent directories exist (e.g., for "Figures/image.png")
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file content
            with open(file_path, "wb") as f:
                f.write(content)

            saved_files[filename] = str(file_path)

        # Create manifest file
        manifest = {
            "arxiv_id": arxiv_id,
            "paper_directory": paper_name,
            "main_tex_file": main_tex_file,
            "files": list(files.keys()),
            "saved_at": datetime.now().isoformat(),
            "total_files": len(files),
        }

        manifest_path = latex_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Saved {len(files)} LaTeX files for {arxiv_id} to {latex_dir}")
        return {
            "directory": str(latex_dir),
            "paper_directory": str(paper_dir),
            "paper_name": paper_name,
            "manifest": str(manifest_path),
            "files": saved_files,
            "main_tex_file": str(latex_dir / main_tex_file),
        }

    def save_markdown_file(
        self,
        arxiv_id: str,
        markdown_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save markdown file with optional YAML frontmatter to paper-centric structure.

        Args:
            arxiv_id: ArXiv paper ID
            markdown_content: Converted markdown content
            metadata: Optional metadata for YAML frontmatter and intelligent filename generation

        Returns:
            Path to saved markdown file
        """
        # Get paper directory name
        paper_name = self._get_paper_directory_name(arxiv_id, metadata)
        paper_dir = self._ensure_paper_directory(paper_name)
        markdown_dir = paper_dir / "markdown"

        # Generate intelligent filename if enabled and metadata available
        if self.use_intelligent_naming and self.filename_generator and metadata:
            filename = self.filename_generator.generate_filename(arxiv_id, metadata, "md")
        else:
            filename = f"{arxiv_id}.md"

        markdown_path = markdown_dir / filename

        # Prepare content with YAML frontmatter if metadata provided
        if metadata:
            yaml_content = self._generate_yaml_frontmatter(metadata)
            full_content = f"{yaml_content}\n\n{markdown_content}"
        else:
            full_content = markdown_content

        # Save markdown file
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Saved markdown file for {arxiv_id} to {markdown_path}")
        return str(markdown_path)

    def save_pdf_file(self, arxiv_id: str, pdf_content: bytes, metadata: dict[str, Any] = None) -> str:
        """Save PDF file to the paper-centric pdf directory.

        Args:
            arxiv_id: ArXiv paper ID
            pdf_content: PDF file content as bytes
            metadata: Optional metadata for intelligent filename generation

        Returns:
            Path to saved PDF file
        """
        # Get paper directory name
        paper_name = self._get_paper_directory_name(arxiv_id, metadata)
        paper_dir = self._ensure_paper_directory(paper_name)
        pdf_dir = paper_dir / "pdf"

        # Generate intelligent filename if enabled and metadata available
        if self.use_intelligent_naming and self.filename_generator and metadata:
            filename = self.filename_generator.generate_filename(arxiv_id, metadata, "pdf")
        else:
            filename = f"{arxiv_id}.pdf"

        pdf_path = pdf_dir / filename

        # Save PDF file
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)

        logger.info(f"Saved PDF file for {arxiv_id} to {pdf_path}")
        return str(pdf_path)

    def save_metadata(self, arxiv_id: str, metadata: dict[str, Any]) -> str:
        """Save paper metadata as JSON file to paper-centric structure.

        Args:
            arxiv_id: ArXiv paper ID
            metadata: Paper metadata dictionary

        Returns:
            Path to saved metadata file
        """
        # Get paper directory name
        paper_name = self._get_paper_directory_name(arxiv_id, metadata)
        paper_dir = self._ensure_paper_directory(paper_name)
        metadata_dir = paper_dir / "metadata"

        metadata_path = metadata_dir / f"{arxiv_id}.json"

        # Add saving timestamp and paper directory info
        enhanced_metadata = metadata.copy()
        enhanced_metadata["saved_at"] = datetime.now().isoformat()
        enhanced_metadata["paper_directory"] = paper_name

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved metadata for {arxiv_id} to {metadata_path}")
        return str(metadata_path)

    def _generate_yaml_frontmatter(self, metadata: dict[str, Any]) -> str:
        """Generate YAML frontmatter from metadata.

        Args:
            metadata: Paper metadata dictionary

        Returns:
            YAML frontmatter string
        """
        import yaml

        # Clean up metadata for YAML
        yaml_metadata = {}

        # Standard fields
        if "title" in metadata:
            yaml_metadata["title"] = metadata["title"]
        if "authors" in metadata:
            yaml_metadata["authors"] = metadata["authors"]
        if "arxiv_id" in metadata:
            yaml_metadata["arxiv_id"] = metadata["arxiv_id"]
        if "categories" in metadata:
            yaml_metadata["categories"] = metadata["categories"]
        if "submitted" in metadata:
            yaml_metadata["submitted"] = metadata["submitted"]
        if "abstract" in metadata:
            yaml_metadata["abstract"] = metadata["abstract"]
        if "keywords" in metadata:
            yaml_metadata["keywords"] = metadata["keywords"]

        # Processing info
        yaml_metadata["processed_at"] = datetime.now().isoformat()
        yaml_metadata["source"] = "arxiv-mcp-improved"

        # Convert to YAML string
        yaml_str = yaml.dump(
            yaml_metadata, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

        return f"---\n{yaml_str}---"

    def get_saved_papers(self) -> dict[str, list[str]]:
        """Get list of saved papers by format from paper-centric structure.

        Returns:
            Dictionary with latex and markdown paper lists
        """
        latex_papers = []
        markdown_papers = []
        pdf_papers = []
        
        if self.output_directory.exists():
            for paper_dir in self.output_directory.iterdir():
                if paper_dir.is_dir():
                    paper_name = paper_dir.name
                    
                    # Check for latex files
                    latex_dir = paper_dir / "latex"
                    if latex_dir.exists() and any(latex_dir.iterdir()):
                        latex_papers.append(paper_name)
                    
                    # Check for markdown files
                    markdown_dir = paper_dir / "markdown" 
                    if markdown_dir.exists() and any(markdown_dir.iterdir()):
                        markdown_papers.append(paper_name)
                    
                    # Check for PDF files
                    pdf_dir = paper_dir / "pdf"
                    if pdf_dir.exists() and any(pdf_dir.iterdir()):
                        pdf_papers.append(paper_name)

        return {
            "latex": latex_papers,
            "markdown": markdown_papers,
            "pdf": pdf_papers,
            "total_latex": len(latex_papers),
            "total_markdown": len(markdown_papers),
            "total_pdf": len(pdf_papers),
        }

    def cleanup_old_files(self, days_old: int = 30) -> dict[str, int]:
        """Clean up files older than specified days.

        Args:
            days_old: Number of days to keep files

        Returns:
            Dictionary with cleanup statistics
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_latex = 0
        cleaned_markdown = 0

        # Clean LaTeX files
        for paper_dir in self.latex_dir.iterdir():
            if paper_dir.is_dir():
                manifest_path = paper_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)

                    saved_at = datetime.fromisoformat(manifest.get("saved_at", ""))
                    if saved_at < cutoff_date:
                        import shutil

                        shutil.rmtree(paper_dir)
                        cleaned_latex += 1

        # Clean markdown files
        for paper_dir in self.markdown_dir.iterdir():
            if paper_dir.is_dir() and paper_dir.stat().st_mtime < cutoff_date.timestamp():
                import shutil

                shutil.rmtree(paper_dir)
                cleaned_markdown += 1

        logger.info(
            f"Cleaned up {cleaned_latex} LaTeX and {cleaned_markdown} markdown paper directories"
        )

        return {
            "cleaned_latex": cleaned_latex,
            "cleaned_markdown": cleaned_markdown,
            "cutoff_days": days_old,
        }
