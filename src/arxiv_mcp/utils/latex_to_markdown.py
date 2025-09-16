"""
LaTeX to Markdown converter with pandoc integration and fallback.
Provides comprehensive LaTeX to Markdown conversion with metadata extraction.
"""

from datetime import datetime
import re
import subprocess
from typing import Any

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

    def __init__(self, use_pandoc: bool = True, pandoc_extra_args: list[str] | None = None):
        self.use_pandoc = use_pandoc and self._check_pandoc_available()
        self.pandoc_extra_args = pandoc_extra_args or []
        logger.info(f"LaTeX to Markdown converter initialized (pandoc: {self.use_pandoc})")

    def _check_pandoc_available(self) -> bool:
        """Check if pandoc is available on the system."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"], check=False, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Pandoc available for conversion")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        logger.warning("Pandoc not available, using fallback converter")
        return False

    def convert(self, latex_content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Convert LaTeX content to Markdown.

        Args:
            latex_content: LaTeX source content
            metadata: Optional metadata for enhanced conversion

        Returns:
            Dictionary with markdown content and conversion info
        """
        if self.use_pandoc:
            return self._convert_with_pandoc(latex_content, metadata)
        return self._convert_with_fallback(latex_content, metadata)

    def _convert_with_pandoc(
        self, latex_content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
                cmd, check=False, input=latex_content, capture_output=True, text=True, timeout=60
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
            logger.error(f"Pandoc conversion failed: {result.stderr}")
            # Fallback to custom converter
            return self._convert_with_fallback(latex_content, metadata)

        except subprocess.TimeoutExpired:
            logger.exception("Pandoc conversion timed out")
            return self._convert_with_fallback(latex_content, metadata)
        except Exception as e:
            logger.exception(f"Pandoc conversion error: {str(e)}")
            return self._convert_with_fallback(latex_content, metadata)

    def _convert_with_fallback(
        self, latex_content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
        # Enhanced comment removal to handle various LaTeX comment patterns
        # Remove % comments but preserve % in math mode (between $ $ or \[ \])
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that are entirely comments
            if line.strip().startswith('%'):
                continue
                
            # Remove inline comments but preserve % in math environments
            # This is a simplified approach - a full solution would need proper LaTeX parsing
            if '%' in line and not ('$' in line or '\\[' in line or '\\(' in line):
                # Find the first % that's not escaped
                comment_pos = line.find('%')
                while comment_pos > 0 and line[comment_pos-1] == '\\':
                    comment_pos = line.find('%', comment_pos + 1)
                if comment_pos != -1:
                    line = line[:comment_pos]
            
            # Skip empty lines from comment removal
            if line.strip():
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)

        # Extract document content (between \\begin{document} and \\end{document})
        doc_match = re.search(r"\\begin{document}(.*?)\\end{document}", content, re.DOTALL)
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
        return re.sub(r"\\subparagraph\{([^}]+)\}", r"##### \\1", content)

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
        return re.sub(r"\\verb\|([^|]+)\|", r"`\\1`", content)

    def _convert_lists(self, content: str) -> str:
        """Convert LaTeX lists to Markdown."""
        # Itemize (unordered lists)
        content = re.sub(r"\\begin\{itemize\}", "", content)
        content = re.sub(r"\\end\{itemize\}", "", content)
        content = re.sub(r"\\item\s+", "- ", content)

        # Enumerate (ordered lists) - simplified
        content = re.sub(r"\\begin\{enumerate\}", "", content)
        return re.sub(r"\\end\{enumerate\}", "", content)
        # Note: This is a simplified conversion; proper numbering would require more complex logic

    def _convert_math(self, content: str) -> str:
        """Convert LaTeX math to Markdown-compatible format with enhanced support."""
        # Inline math - handle various forms
        content = re.sub(r"\$([^$]+)\$", r"$\1$", content)  # Single $ (inline math)
        content = re.sub(r"\\\(([^)]+)\\\)", r"$\1$", content)  # \( \) (inline math)

        # Display math environments - enhanced coverage
        content = re.sub(
            r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
            r"$$\1$$",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(
            r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", r"$$\1$$", content, flags=re.DOTALL
        )
        content = re.sub(
            r"\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}",
            r"$$\1$$",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(
            r"\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}",
            r"$$\1$$",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(
            r"\\begin\{multline\*?\}(.*?)\\end\{multline\*?\}",
            r"$$\1$$",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(
            r"\\begin\{split\}(.*?)\\end\{split\}",
            r"$$\1$$",
            content,
            flags=re.DOTALL,
        )

        # Display math with delimiters
        content = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", content, flags=re.DOTALL)
        content = re.sub(r"\$\$(.*?)\$\$", r"$$\1$$", content, flags=re.DOTALL)  # Clean double $$

        # Handle common math commands that need preservation
        content = re.sub(
            r"\\displaystyle\s+", "", content
        )  # Remove displaystyle as it's implied in $$
        content = re.sub(r"\\textstyle\s+", "", content)  # Remove textstyle

        # Clean up alignment characters that don't work in markdown
        content = re.sub(r"&\s*=\s*&", " = ", content)  # Alignment ampersands
        return re.sub(r"\\\\\\\\", r"\\\\", content)  # Double newlines in equations

    def _convert_figures(self, content: str) -> str:
        """Convert LaTeX figures to Markdown with improved format handling."""
        # Enhanced figure conversion
        figure_pattern = r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}"

        def replace_figure(match):
            figure_content = match.group(1)

            # Extract includegraphics with better pattern matching
            img_match = re.search(r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}", figure_content)
            if img_match:
                img_match.group(1) or ""
                img_path = img_match.group(2)

                # Improve image path handling
                img_path = self._improve_image_path(img_path)

                # Extract caption with better cleaning
                caption_match = re.search(r"\\caption\{([^}]+)\}", figure_content)
                caption = ""
                if caption_match:
                    caption = caption_match.group(1)
                    # Clean up caption LaTeX commands more thoroughly
                    caption = self._clean_latex_commands(caption)

                # Extract label for cross-referencing
                label_match = re.search(r"\\label\{([^}]+)\}", figure_content)
                label = label_match.group(1) if label_match else ""

                # Build markdown figure
                if caption and label:
                    return f'![{caption}]({img_path})\n<a id="{label}"></a>'
                if caption:
                    return f"![{caption}]({img_path})"
                if label:
                    return f'![]({img_path})\n<a id="{label}"></a>'
                return f"![]({img_path})"

            # Handle subfigures
            subfig_pattern = r"\\begin\{subfigure\}.*?\\end\{subfigure\}"
            if re.search(subfig_pattern, figure_content, re.DOTALL):
                subfigs = re.findall(
                    r"\\begin\{subfigure\}.*?\\includegraphics.*?\{([^}]+)\}.*?\\end\{subfigure\}",
                    figure_content,
                    re.DOTALL,
                )
                if subfigs:
                    improved_paths = [self._improve_image_path(path) for path in subfigs]
                    subfig_markdown = " | ".join([f"![]({path})" for path in improved_paths])
                    return f"{subfig_markdown}\n\n*Subfigures*"

            return "[Figure - Complex figure layout not fully supported]"

        content = re.sub(figure_pattern, replace_figure, content, flags=re.DOTALL)

        # Handle standalone includegraphics outside figure environments
        standalone_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"

        def replace_standalone(match):
            img_path = self._improve_image_path(match.group(1))
            return f"![]({img_path})"

        return re.sub(standalone_pattern, replace_standalone, content)

    def _improve_image_path(self, img_path: str) -> str:
        """Improve image path for better Markdown compatibility."""
        # Remove file extensions that don't work well in Markdown
        if img_path.endswith((".ps", ".eps")):
            # Suggest PNG alternative
            base_name = img_path.rsplit(".", 1)[0]
            return f"{base_name}.png"
        if img_path.endswith(".pdf"):
            # Convert PDF figures to PNG for better display
            base_name = img_path.rsplit(".", 1)[0]
            return f"{base_name}.png"

        # Keep original path for supported formats
        return img_path

    def _clean_latex_commands(self, text: str) -> str:
        """Clean LaTeX commands from text for better Markdown display."""
        # Remove common LaTeX commands that don't translate well
        text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)  # \command{content} -> content
        text = re.sub(r"\\[a-zA-Z]+", "", text)  # \command -> empty
        text = re.sub(r"\s+", " ", text)  # normalize whitespace
        return text.strip()

    def _convert_tables(self, content: str) -> str:
        """Convert LaTeX tables to Markdown with improved support."""

        # Enhanced table conversion for simple cases
        def replace_tabular(match):
            table_content = match.group(1)

            # Extract table specification (column alignment)
            spec_match = re.search(r"\\begin\{tabular\}\{([^}]+)\}", match.group(0))
            if not spec_match:
                return "[Table - Complex table conversion not supported]"

            # Count columns from specification
            spec = spec_match.group(1)
            num_cols = len([c for c in spec if c in "lcr"])

            if num_cols == 0:
                return "[Table - Invalid table specification]"

            # Try to convert simple tables
            lines = table_content.split("\\\\")
            markdown_rows = []

            for i, line in enumerate(lines):
                if not line.strip():
                    continue

                # Remove LaTeX commands and split by &
                clean_line = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", line)
                clean_line = re.sub(r"\\[a-zA-Z]+", "", clean_line)
                cells = [cell.strip() for cell in clean_line.split("&")]

                # Pad or trim to expected number of columns
                while len(cells) < num_cols:
                    cells.append("")
                cells = cells[:num_cols]

                markdown_rows.append("| " + " | ".join(cells) + " |")

                # Add header separator after first row
                if i == 0:
                    separator = "|" + "".join([" --- |" for _ in range(num_cols)])
                    markdown_rows.append(separator)

            if markdown_rows:
                return "\n".join(markdown_rows)
            return "[Table - Content extraction failed]"

        # Handle tabular environments
        content = re.sub(
            r"\\begin\{tabular\}.*?\\end\{tabular\}",
            replace_tabular,
            content,
            flags=re.DOTALL,
        )

        # Handle other table environments with simpler fallback
        content = re.sub(
            r"\\begin\{array\}.*?\\end\{array\}",
            "[Array/Matrix - LaTeX array conversion not fully supported]",
            content,
            flags=re.DOTALL,
        )
        return re.sub(
            r"\\begin\{matrix\}.*?\\end\{matrix\}",
            "[Matrix - LaTeX matrix conversion not fully supported]",
            content,
            flags=re.DOTALL,
        )

    def _convert_citations(self, content: str) -> str:
        """Convert LaTeX citations to Markdown format."""
        # Simple citation conversion
        content = re.sub(r"\\cite\{([^}]+)\}", r"[@\\1]", content)
        content = re.sub(r"\\citep\{([^}]+)\}", r"[@\\1]", content)
        return re.sub(r"\\citet\{([^}]+)\}", r"@\\1", content)

    def _convert_references(self, content: str) -> str:
        """Convert LaTeX references to Markdown."""
        content = re.sub(r"\\ref\{([^}]+)\}", r"[\\1](#\\1)", content)
        return re.sub(r"\\label\{([^}]+)\}", r'<a id="\\1"></a>', content)

    def _cleanup_markdown(self, content: str) -> str:
        """Clean up the converted markdown."""
        # Remove remaining LaTeX commands
        content = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\\1", content)
        content = re.sub(r"\\[a-zA-Z]+", "", content)

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\\n\\n", content)
        content = re.sub(r"[ \\t]+", " ", content)

        # Remove empty lines at start and end
        return content.strip()

    def _post_process_markdown(self, markdown: str) -> str:
        """Post-process pandoc-generated markdown."""
        # Clean up excessive blank lines
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        
        # Enhanced abstract cleaning for YAML frontmatter
        if markdown.startswith('---'):
            # Split YAML frontmatter and content
            parts = markdown.split('---', 2)
            if len(parts) >= 3:
                yaml_section = parts[1]
                content_section = parts[2]
                
                # Clean up abstract in YAML section
                yaml_section = self._clean_yaml_abstract(yaml_section)
                
                # Clean up figure references in content
                content_section = self._clean_figure_references(content_section)
                
                # Add document structure improvements
                content_section = self._enhance_document_structure(content_section)
                
                # Reassemble
                markdown = f"---{yaml_section}---{content_section}"
        else:
            # Clean figure references in content without YAML
            markdown = self._clean_figure_references(markdown)
            # Add document structure improvements
            markdown = self._enhance_document_structure(markdown)
        
        # Fix common pandoc issues
        # (Add specific post-processing rules as needed)

        return markdown.strip()
    
    def _clean_figure_references(self, content: str) -> str:
        """Clean up malformed figure references generated by pandoc."""
        # Fix complex figure references like: Fig.[\[fig:1\]](#fig:1){reference-type="ref" reference="fig:1"}
        fig_ref_pattern = r'Fig\.\[\\\[\s*([^\\]+)\s*\\\]\]\(#[^)]+\)\{[^}]*\}'
        content = re.sub(fig_ref_pattern, r'Figure \1', content)
        
        # Fix simpler figure references like: [\[fig:1\]](#fig:1){reference-type="ref" reference="fig:1"}
        simple_ref_pattern = r'\[\\\[\s*([^\\]+)\s*\\\]\]\(#[^)]+\)\{[^}]*\}'
        content = re.sub(simple_ref_pattern, r'\1', content)
        
        # Fix escaped figure labels in general
        escaped_fig_pattern = r'\\\[\s*([^\\]+)\s*\\\]'
        content = re.sub(escaped_fig_pattern, r'\1', content)
        
        # Clean up any remaining reference artifacts
        ref_artifact_pattern = r'\{reference-type="[^"]*"\s*reference="[^"]*"\}'
        content = re.sub(ref_artifact_pattern, '', content)
        
        # Improve figure references from "Figure fig:1" to "Figure 1"
        fig_label_pattern = r'Figure\s+fig:(\d+)'
        content = re.sub(fig_label_pattern, r'Figure \1', content)
        
        # Also handle table references
        table_ref_pattern = r'Table\s+tab:(\d+)'
        content = re.sub(table_ref_pattern, r'Table \1', content)
        
        # Handle equation references
        eq_ref_pattern = r'Equation\s+eq:(\d+)'
        content = re.sub(eq_ref_pattern, r'Equation \1', content)
        
        return content
    
    def _enhance_document_structure(self, content: str) -> str:
        """Enhance document structure with table of contents and proper organization."""
        lines = content.split('\n')
        enhanced_lines = []
        headings = []
        
        # First pass: collect headings and improve structure
        for line in lines:
            # Detect headings
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading_text = line.strip('#').strip()
                
                # Create anchor ID from heading text
                anchor_id = re.sub(r'[^\w\s-]', '', heading_text.lower())
                anchor_id = re.sub(r'[\s_]+', '-', anchor_id)
                
                # Store heading info for TOC
                headings.append({
                    'level': level,
                    'text': heading_text,
                    'anchor': anchor_id
                })
                
                # Enhance heading with anchor
                enhanced_line = f"{'#' * level} {heading_text} {{#{anchor_id}}}"
                enhanced_lines.append(enhanced_line)
            else:
                enhanced_lines.append(line)
        
        # Generate table of contents if there are headings
        if len(headings) > 2:  # Only add TOC if there are meaningful sections
            toc_lines = ["\n## Table of Contents\n"]
            
            for heading in headings:
                # Skip the first heading if it's the title (level 1)
                if heading['level'] == 1:
                    continue
                    
                indent = "  " * (heading['level'] - 2)  # Adjust indentation
                toc_line = f"{indent}- [{heading['text']}](#{heading['anchor']})"
                toc_lines.append(toc_line)
            
            toc_lines.append("")  # Add blank line after TOC
            
            # Insert TOC after the first few lines (after title/intro if present)
            insert_pos = 0
            for i, line in enumerate(enhanced_lines[:10]):  # Look in first 10 lines
                if line.strip().startswith('#') and enhanced_lines[i].count('#') == 1:
                    # Found title, insert TOC after next non-empty section
                    for j in range(i + 1, min(i + 5, len(enhanced_lines))):
                        if enhanced_lines[j].strip() and not enhanced_lines[j].startswith('#'):
                            # Find end of this paragraph
                            for k in range(j, len(enhanced_lines)):
                                if enhanced_lines[k].strip() == "":
                                    insert_pos = k
                                    break
                            break
                    break
            
            if insert_pos > 0:
                enhanced_lines = enhanced_lines[:insert_pos] + toc_lines + enhanced_lines[insert_pos:]
        
        return '\n'.join(enhanced_lines)
    
    def _clean_yaml_abstract(self, yaml_section: str) -> str:
        """Clean up abstract field in YAML frontmatter."""
        import re
        
        # Pattern to match abstract field (handles multiline abstracts)
        abstract_pattern = r'(abstract:\s*[\'"]?)(.*?)([\'"]?\s*(?=\n[a-zA-Z]|\n---|\Z))'
        
        def clean_abstract_content(match):
            prefix = match.group(1)
            abstract_content = match.group(2)
            suffix = match.group(3)
            
            # Remove % comments and incomplete fragments
            abstract_lines = abstract_content.split('\n')
            cleaned_lines = []
            
            for line in abstract_lines:
                line = line.strip()
                
                # Skip lines that start with % (comment lines)
                if line.startswith('%'):
                    continue
                    
                # Remove % comments from the end of lines
                if '%' in line:
                    comment_pos = line.find('%')
                    # Make sure it's not escaped
                    while comment_pos > 0 and line[comment_pos-1] == '\\':
                        comment_pos = line.find('%', comment_pos + 1)
                    if comment_pos != -1:
                        line = line[:comment_pos].strip()
                
                # Skip empty lines or lines with just punctuation
                if line and not line.isspace() and len(line.strip()) > 2:
                    cleaned_lines.append(line)
            
            # Join lines and clean up
            cleaned_abstract = ' '.join(cleaned_lines)
            
            # Remove common LaTeX artifacts
            cleaned_abstract = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', cleaned_abstract)
            cleaned_abstract = re.sub(r'\\[a-zA-Z]+', '', cleaned_abstract)
            
            # Clean up multiple spaces and normalize punctuation
            cleaned_abstract = re.sub(r'\s+', ' ', cleaned_abstract)
            cleaned_abstract = cleaned_abstract.strip()
            
            return f"{prefix}{cleaned_abstract}{suffix}"
        
        return re.sub(abstract_pattern, clean_abstract_content, yaml_section, flags=re.DOTALL)

    def extract_metadata_from_latex(self, latex_content: str) -> dict[str, Any]:
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
        self, latex_content: str, arxiv_id: str | None = None
    ) -> dict[str, Any]:
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
