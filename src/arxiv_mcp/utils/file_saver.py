"""
File saving utilities for ArXiv papers.
Handles saving LaTeX files, markdown files, and metadata to organized directory structure.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logging import structured_logger

logger = structured_logger()


class FileSaver:
    """Handles saving ArXiv papers in organized directory structure."""

    def __init__(self, output_directory: str = "./output"):
        self.output_directory = Path(output_directory)
        self.latex_dir = self.output_directory / "latex"
        self.markdown_dir = self.output_directory / "markdown"
        self.metadata_dir = self.output_directory / "metadata"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create output directories if they don't exist."""
        for directory in [self.latex_dir, self.markdown_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directories ensured: {self.output_directory}")

    def save_latex_files(
        self, arxiv_id: str, files: Dict[str, bytes], main_tex_file: str
    ) -> Dict[str, str]:
        """Save LaTeX files to organized directory structure.

        Args:
            arxiv_id: ArXiv paper ID
            files: Dictionary of filename -> file content
            main_tex_file: Name of the main .tex file

        Returns:
            Dictionary with saved file paths
        """
        paper_dir = self.latex_dir / arxiv_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        for filename, content in files.items():
            file_path = paper_dir / filename

            # Save file content
            with open(file_path, "wb") as f:
                f.write(content)

            saved_files[filename] = str(file_path)

        # Create manifest file
        manifest = {
            "arxiv_id": arxiv_id,
            "main_tex_file": main_tex_file,
            "files": list(files.keys()),
            "saved_at": datetime.now().isoformat(),
            "total_files": len(files),
        }

        manifest_path = paper_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Saved {len(files)} LaTeX files for {arxiv_id} to {paper_dir}")
        return {
            "directory": str(paper_dir),
            "manifest": str(manifest_path),
            "files": saved_files,
            "main_tex_file": str(paper_dir / main_tex_file),
        }

    def save_markdown_file(
        self,
        arxiv_id: str,
        markdown_content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save markdown file with optional YAML frontmatter.

        Args:
            arxiv_id: ArXiv paper ID
            markdown_content: Converted markdown content
            metadata: Optional metadata for YAML frontmatter

        Returns:
            Path to saved markdown file
        """
        paper_dir = self.markdown_dir / arxiv_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = paper_dir / f"{arxiv_id}.md"

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

    def save_metadata(self, arxiv_id: str, metadata: Dict[str, Any]) -> str:
        """Save paper metadata as JSON file.

        Args:
            arxiv_id: ArXiv paper ID
            metadata: Paper metadata dictionary

        Returns:
            Path to saved metadata file
        """
        metadata_path = self.metadata_dir / f"{arxiv_id}.json"

        # Add saving timestamp
        metadata["saved_at"] = datetime.now().isoformat()

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved metadata for {arxiv_id} to {metadata_path}")
        return str(metadata_path)

    def _generate_yaml_frontmatter(self, metadata: Dict[str, Any]) -> str:
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

    def get_saved_papers(self) -> Dict[str, List[str]]:
        """Get list of saved papers by format.

        Returns:
            Dictionary with latex and markdown paper lists
        """
        latex_papers = []
        if self.latex_dir.exists():
            latex_papers = [d.name for d in self.latex_dir.iterdir() if d.is_dir()]

        markdown_papers = []
        if self.markdown_dir.exists():
            markdown_papers = [d.name for d in self.markdown_dir.iterdir() if d.is_dir()]

        return {
            "latex": latex_papers,
            "markdown": markdown_papers,
            "total_latex": len(latex_papers),
            "total_markdown": len(markdown_papers),
        }

    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, int]:
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
                    with open(manifest_path, "r") as f:
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
