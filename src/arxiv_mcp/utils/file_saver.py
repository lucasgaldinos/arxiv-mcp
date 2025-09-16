"""
File saving utilities for ArXiv papers.
Handles saving LaTeX files, markdown files, and metadata to organized directory structure.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ..utils.logging import structured_logger

logger = structured_logger()


class FileSaver:
    """Handles saving ArXiv papers in organized directory structure."""

    def __init__(self, output_directory: str | None = None):
        if output_directory:
            self.output_directory = Path(output_directory)
        else:
            # Import here to avoid circular imports
            from ..core.enhanced_config import ConfigurationManager
            config = ConfigurationManager.load_config()
            self.output_directory = Path(config.output_directory)
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
        self, arxiv_id: str, files: dict[str, bytes], main_tex_file: str
    ) -> dict[str, str]:
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
        metadata: dict[str, Any] | None = None,
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

        # Check if markdown already has YAML frontmatter (from pandoc)
        if markdown_content.strip().startswith('---') and metadata:
            # Enhance existing YAML frontmatter instead of duplicating
            full_content = self._enhance_existing_yaml(markdown_content, metadata, arxiv_id)
        elif metadata:
            # Generate new YAML frontmatter
            yaml_content = self._generate_yaml_frontmatter(metadata)
            full_content = f"{yaml_content}\n\n{markdown_content}"
        else:
            full_content = markdown_content

        # Save markdown file
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Saved markdown file for {arxiv_id} to {markdown_path}")
        return str(markdown_path)

    def save_metadata(self, arxiv_id: str, metadata: dict[str, Any]) -> str:
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

    def _enhance_existing_yaml(self, markdown_content: str, metadata: dict[str, Any], arxiv_id: str) -> str:
        """Enhance existing YAML frontmatter with additional metadata.
        
        Args:
            markdown_content: Markdown content with existing YAML frontmatter
            metadata: Additional metadata to merge
            arxiv_id: ArXiv paper ID
            
        Returns:
            Enhanced markdown content with merged YAML frontmatter
        """
        import yaml
        
        # Split the content into YAML and body
        parts = markdown_content.split('---', 2)
        if len(parts) < 3:
            # No valid YAML frontmatter found, fall back to adding new one
            yaml_content = self._generate_yaml_frontmatter(metadata)
            return f"{yaml_content}\n\n{markdown_content}"
        
        yaml_section = parts[1].strip()
        body_section = parts[2]
        
        try:
            # Parse existing YAML
            existing_yaml = yaml.safe_load(yaml_section) or {}
            
            # Add ArXiv ID and processing metadata
            existing_yaml['arxiv_id'] = arxiv_id
            existing_yaml['processed_at'] = datetime.now().isoformat()
            existing_yaml['source'] = 'arxiv-mcp-improved'
            
            # Add categories if available in metadata
            if 'categories' in metadata and metadata['categories']:
                existing_yaml['categories'] = metadata['categories']
            
            # Add keywords if available
            if 'keywords' in metadata and metadata['keywords']:
                existing_yaml['keywords'] = metadata['keywords']
            
            # Add submission date if available
            if 'submitted' in metadata and metadata['submitted']:
                existing_yaml['submitted'] = metadata['submitted']
                
            # Convert back to YAML
            enhanced_yaml = yaml.dump(
                existing_yaml, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            
            return f"---\n{enhanced_yaml}---{body_section}"
            
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse existing YAML frontmatter: {e}")
            # Fall back to generating new YAML
            yaml_content = self._generate_yaml_frontmatter(metadata)
            return f"{yaml_content}\n\n{body_section}"

    def get_saved_papers(self) -> dict[str, list[str]]:
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
