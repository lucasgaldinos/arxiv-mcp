"""
LaTeX to Markdown converter with pandoc integration and fallback.
Provides comprehensive LaTeX to Markdown conversion with metadata extraction.
"""

import re
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.logging import structured_logger

logger = structured_logger()

# Check if pandoc is available
def check_pandoc_available() -> bool:
    """Check if pandoc is available on the system."""
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

PANDOC_AVAILABLE = check_pandoc_available()


class LaTeXToMarkdownConverter:
    """Converts LaTeX content to Markdown with multiple conversion strategies."""

    def __init__(
        self, use_pandoc: bool = True, pandoc_extra_args: Optional[List[str]] = None
    ):
        self.use_pandoc = use_pandoc and self._check_pandoc_available()
        self.pandoc_extra_args = pandoc_extra_args or []
        logger.info(
            f"LaTeX to Markdown converter initialized (pandoc: {self.use_pandoc})"
        )

    def _check_pandoc_available(self) -> bool:
        """Check if pandoc is available on the system."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Pandoc available for conversion")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        logger.warning("Pandoc not available, using fallback converter")
        return False

    def convert(
        self, latex_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert LaTeX content to Markdown.

        Args:
            latex_content: LaTeX source content
            metadata: Optional metadata for enhanced conversion

        Returns:
            Dictionary with markdown content and conversion info
        """
        if self.use_pandoc:
            return self._convert_with_pandoc(latex_content, metadata)
        else:
            return self._convert_with_fallback(latex_content, metadata)

    def _convert_with_pandoc(
        self, latex_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert LaTeX to Markdown using pandoc."""
        try:
            # Prepare pandoc command
            cmd = [
                "pandoc",
                "--from=latex",
                "--to=markdown",
                "--wrap=none",  # Don't wrap lines
                "--standalone",  # Include document headers
                *self.pandoc_extra_args,
            ]

            # Run pandoc conversion
            result = subprocess.run(
                cmd, input=latex_content, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                markdown_content = result.stdout

                # Post-process the markdown
                markdown_content = self._post_process_markdown(markdown_content)

                logger.info("Successfully converted LaTeX to Markdown using pandoc")
                return {
                    "markdown": markdown_content,
                    "method": "pandoc",
                    "success": True,
                    "warnings": result.stderr if result.stderr else None,
                }
            else:
                logger.error(f"Pandoc conversion failed: {result.stderr}")
                # Fallback to custom converter
                return self._convert_with_fallback(latex_content, metadata)

        except subprocess.TimeoutExpired:
            logger.error("Pandoc conversion timed out")
            return self._convert_with_fallback(latex_content, metadata)
        except Exception as e:
            logger.error(f"Pandoc conversion error: {str(e)}")
            return self._convert_with_fallback(latex_content, metadata)

    def _convert_with_fallback(
        self, latex_content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert LaTeX to Markdown using custom fallback converter."""
        logger.info("Using fallback LaTeX to Markdown converter")

        # Clean the LaTeX content
        markdown = self._clean_latex_content(latex_content)

        # Convert common LaTeX elements
        markdown = self._convert_sections(markdown)
        markdown = self._convert_emphasis(markdown)
        markdown = self._convert_lists(markdown)
        markdown = self._convert_math(markdown)
        markdown = self._convert_figures(markdown)
        markdown = self._convert_tables(markdown)
        markdown = self._convert_citations(markdown)
        markdown = self._convert_references(markdown)

        # Clean up final markdown
        markdown = self._cleanup_markdown(markdown)

        return {
            "markdown": markdown,
            "method": "fallback",
            "success": True,
            "warnings": "Converted using fallback method - some formatting may be lost",
        }

    def _clean_latex_content(self, content: str) -> str:
        """Clean LaTeX content by removing comments and preamble."""
        # Remove comments
        content = re.sub(r"%.*$", "", content, flags=re.MULTILINE)

        # Extract document content (between \\begin{document} and \\end{document})
        doc_match = re.search(
            r"\\begin{document}(.*?)\\end{document}", content, re.DOTALL
        )
        if doc_match:
            content = doc_match.group(1)

        return content.strip()

    def _convert_sections(self, content: str) -> str:
        """Convert LaTeX section commands to Markdown headers."""
        # Section levels
        content = re.sub(r"\\section\*?\{([^}]+)\}", r"# \\1", content)
        content = re.sub(r"\\subsection\*?\{([^}]+)\}", r"## \\1", content)
        content = re.sub(r"\\subsubsection\*?\{([^}]+)\}", r"### \\1", content)
        content = re.sub(r"\\paragraph\{([^}]+)\}", r"#### \\1", content)
        content = re.sub(r"\\subparagraph\{([^}]+)\}", r"##### \\1", content)

        return content

    def _convert_emphasis(self, content: str) -> str:
        """Convert LaTeX emphasis to Markdown."""
        # Bold
        content = re.sub(r"\\textbf\{([^}]+)\}", r"**\\1**", content)
        content = re.sub(r"\\bf\{([^}]+)\}", r"**\\1**", content)

        # Italics
        content = re.sub(r"\\textit\{([^}]+)\}", r"*\\1*", content)
        content = re.sub(r"\\emph\{([^}]+)\}", r"*\\1*", content)
        content = re.sub(r"\\it\{([^}]+)\}", r"*\\1*", content)

        # Typewriter/code
        content = re.sub(r"\\texttt\{([^}]+)\}", r"`\\1`", content)
        content = re.sub(r"\\verb\|([^|]+)\|", r"`\\1`", content)

        return content

    def _convert_lists(self, content: str) -> str:
        """Convert LaTeX lists to Markdown."""
        # Itemize (unordered lists)
        content = re.sub(r"\\begin\{itemize\}", "", content)
        content = re.sub(r"\\end\{itemize\}", "", content)
        content = re.sub(r"\\item\s+", "- ", content)

        # Enumerate (ordered lists) - simplified
        content = re.sub(r"\\begin\{enumerate\}", "", content)
        content = re.sub(r"\\end\{enumerate\}", "", content)
        # Note: This is a simplified conversion; proper numbering would require more complex logic

        return content

    def _convert_math(self, content: str) -> str:
        """Convert LaTeX math to Markdown-compatible format."""
        # Inline math - keep as is (many markdown processors support LaTeX math)
        # Display math environments
        content = re.sub(
            r"\\begin\{equation\}(.*?)\\end\{equation\}",
            r"$$\\1$$",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(
            r"\\begin\{align\}(.*?)\\end\{align\}", r"$$\\1$$", content, flags=re.DOTALL
        )
        content = re.sub(
            r"\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}",
            r"$$\\1$$",
            content,
            flags=re.DOTALL,
        )

        # Display math with \\[ \\]
        content = re.sub(r"\\\\\\[(.*?)\\\\\\]", r"$$\\1$$", content, flags=re.DOTALL)

        return content

    def _convert_figures(self, content: str) -> str:
        """Convert LaTeX figures to Markdown."""
        # Simple figure conversion
        figure_pattern = r"\\begin\{figure\}(.*?)\\end\{figure\}"

        def replace_figure(match):
            figure_content = match.group(1)

            # Extract includegraphics
            img_match = re.search(
                r"\\includegraphics(?:\\[.*?\\])?\{([^}]+)\}", figure_content
            )
            if img_match:
                img_path = img_match.group(1)

                # Extract caption
                caption_match = re.search(r"\\caption\{([^}]+)\}", figure_content)
                caption = caption_match.group(1) if caption_match else ""

                if caption:
                    return f"![{caption}]({img_path})"
                else:
                    return f"![]({img_path})"

            return "[Figure]"

        content = re.sub(figure_pattern, replace_figure, content, flags=re.DOTALL)

        return content

    def _convert_tables(self, content: str) -> str:
        """Convert simple LaTeX tables to Markdown."""
        # This is a simplified table conversion
        # Full table conversion would require more sophisticated parsing
        content = re.sub(
            r"\\begin\{tabular\}.*?\\end\{tabular\}",
            "[Table - LaTeX table conversion not fully supported]",
            content,
            flags=re.DOTALL,
        )

        return content

    def _convert_citations(self, content: str) -> str:
        """Convert LaTeX citations to Markdown format."""
        # Simple citation conversion
        content = re.sub(r"\\cite\{([^}]+)\}", r"[@\\1]", content)
        content = re.sub(r"\\citep\{([^}]+)\}", r"[@\\1]", content)
        content = re.sub(r"\\citet\{([^}]+)\}", r"@\\1", content)

        return content

    def _convert_references(self, content: str) -> str:
        """Convert LaTeX references to Markdown."""
        content = re.sub(r"\\ref\{([^}]+)\}", r"[\\1](#\\1)", content)
        content = re.sub(r"\\label\{([^}]+)\}", r'<a id="\\1"></a>', content)

        return content

    def _cleanup_markdown(self, content: str) -> str:
        """Clean up the converted markdown."""
        # Remove remaining LaTeX commands
        content = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\\1", content)
        content = re.sub(r"\\[a-zA-Z]+", "", content)

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\\n\\n", content)
        content = re.sub(r"[ \\t]+", " ", content)

        # Remove empty lines at start and end
        content = content.strip()

        return content

    def _post_process_markdown(self, markdown: str) -> str:
        """Post-process pandoc-generated markdown."""
        # Clean up excessive blank lines
        markdown = re.sub(r"\n{3,}", "\\n\\n", markdown)

        # Fix common pandoc issues
        # (Add specific post-processing rules as needed)

        return markdown.strip()

    def extract_metadata_from_latex(self, latex_content: str) -> Dict[str, Any]:
        """Extract metadata from LaTeX content.

        Args:
            latex_content: LaTeX source content

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}

        # Extract title
        title_match = re.search(r"\\title\{([^}]+)\}", latex_content)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extract authors
        author_match = re.search(r"\\author\{([^}]+)\}", latex_content)
        if author_match:
            authors_str = author_match.group(1)
            # Simple author parsing (could be enhanced)
            authors = [a.strip() for a in re.split(r"\\and|,", authors_str)]
            metadata["authors"] = [a for a in authors if a]

        # Extract abstract
        abstract_match = re.search(
            r"\\begin\{abstract\}(.*?)\\end\{abstract\}", latex_content, re.DOTALL
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # Clean LaTeX commands from abstract
            abstract = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\\1", abstract)
            abstract = re.sub(r"\\[a-zA-Z]+", "", abstract)
            metadata["abstract"] = abstract.strip()

        # Extract keywords
        keywords_match = re.search(r"\\keywords\{([^}]+)\}", latex_content)
        if keywords_match:
            keywords_str = keywords_match.group(1)
            keywords = [k.strip() for k in keywords_str.split(",")]
            metadata["keywords"] = [k for k in keywords if k]

        # Extract date
        date_match = re.search(r"\\date\{([^}]+)\}", latex_content)
        if date_match:
            metadata["date"] = date_match.group(1).strip()

        return metadata

    def convert_with_metadata(
        self, latex_content: str, arxiv_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert LaTeX to Markdown and extract metadata.

        Args:
            latex_content: LaTeX source content
            arxiv_id: Optional ArXiv ID for metadata

        Returns:
            Dictionary with markdown content, metadata, and conversion info
        """
        # Extract metadata from LaTeX
        metadata = self.extract_metadata_from_latex(latex_content)

        # Add ArXiv ID if provided
        if arxiv_id:
            metadata["arxiv_id"] = arxiv_id

        # Add processing timestamp
        metadata["processed_at"] = datetime.now().isoformat()

        # Convert to markdown
        conversion_result = self.convert(latex_content, metadata)

        return {
            "markdown": conversion_result["markdown"],
            "metadata": metadata,
            "conversion_method": conversion_result["method"],
            "success": conversion_result["success"],
            "warnings": conversion_result.get("warnings"),
        }
