"""
Intelligent filename generator for ArXiv papers using metadata.
Generates human-readable, filesystem-safe filenames in kebab-case format.
"""

import re
from pathlib import Path
from typing import Any
from datetime import datetime


class FilenameGenerator:
    """Generate intelligent filenames for ArXiv papers using metadata."""

    MAX_FILENAME_LENGTH = 200  # Conservative limit for cross-platform compatibility
    MAX_COMPONENT_LENGTH = 50  # Max length for individual components

    def __init__(self):
        # Common words to remove from titles for cleaner filenames
        self.stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "has", "he", "in", "is", "it", "its", "of", "on",
            "that", "the", "to", "was", "were", "will", "with", "using"
        }

        # ArXiv category to field mapping
        self.category_to_field = {
            # Computer Science
            "cs.ai": "ai", "cs.cl": "nlp", "cs.cv": "vision", "cs.lg": "ml",
            "cs.ne": "neuro", "cs.ro": "robotics", "cs.cr": "crypto",
            "cs.dc": "distributed", "cs.ds": "algorithms", "cs.gr": "graphics",
            "cs.hc": "hci", "cs.ir": "information", "cs.pl": "programming",
            "cs.se": "software", "cs.sy": "systems",
            
            # Physics
            "physics.comp-ph": "physics", "physics.data-an": "data",
            "physics.ins-det": "instrumentation", "physics.optics": "optics",
            "cond-mat": "condensed", "astro-ph": "astrophysics",
            "hep-ph": "particles", "nucl-th": "nuclear", "quant-ph": "quantum",
            
            # Mathematics
            "math.oc": "optimization", "math.st": "statistics", "math.na": "numerical",
            "math.pr": "probability", "math.ag": "algebra", "math.co": "combinatorics",
            
            # Biology and others
            "q-bio": "biology", "stat": "statistics", "econ": "economics"
        }

    def generate_filename(self, arxiv_id: str, metadata: dict[str, Any], extension: str = "pdf") -> str:
        """Generate intelligent filename from ArXiv metadata.
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., "2412.08992v1")
            metadata: Paper metadata dictionary
            extension: File extension (default: "pdf")
            
        Returns:
            Intelligent filename in format: author-title-year-field.extension
        """
        # Extract components
        author = self._extract_primary_author(metadata.get("authors", []))
        title = self._clean_title(metadata.get("title", ""))
        year = self._extract_year(arxiv_id, metadata)
        field = self._extract_field(metadata.get("categories", []))
        
        # Build filename components
        components = []
        
        if author:
            components.append(author)
        if title:
            components.append(title)
        if year:
            components.append(year)
        if field:
            components.append(field)
            
        # If no meaningful components, fall back to arxiv_id
        if not components:
            return f"{arxiv_id}.{extension}"
            
        # Join components and add extension
        base_filename = "-".join(components)
        filename = f"{base_filename}.{extension}"
        
        # Ensure filename length is reasonable
        if len(filename) > self.MAX_FILENAME_LENGTH:
            filename = self._truncate_filename(base_filename, extension)
            
        return filename

    def _extract_primary_author(self, authors: list[str]) -> str:
        """Extract and clean the primary (first) author's last name.
        
        Args:
            authors: List of author names (may contain LaTeX formatting)
            
        Returns:
            Cleaned last name in kebab-case
        """
        if not authors:
            return ""
            
        first_author = authors[0]
        
        # Remove LaTeX formatting
        cleaned = self._remove_latex_formatting(first_author)
        
        # Handle multiple authors in one string (separated by "and")
        if " and " in cleaned:
            cleaned = cleaned.split(" and ")[0].strip()
            
        # Extract last name (assuming "First Last" or "Last, First" format)
        if "," in cleaned:
            # "Last, First" format
            last_name = cleaned.split(",")[0].strip()
        else:
            # "First Last" format - take last word
            words = cleaned.split()
            if words:
                # Skip titles and get actual last name
                meaningful_words = [w for w in words if w.lower() not in {"dr", "prof", "mr", "ms", "mrs"}]
                last_name = meaningful_words[-1] if meaningful_words else words[-1]
            else:
                last_name = ""
            
        # Clean and convert to kebab-case
        last_name = self._to_kebab_case(last_name)
        
        # Truncate if too long
        if len(last_name) > self.MAX_COMPONENT_LENGTH:
            last_name = last_name[:self.MAX_COMPONENT_LENGTH].rstrip("-")
            
        return last_name

    def _clean_title(self, title: str) -> str:
        """Clean and shorten paper title for filename use.
        
        Args:
            title: Paper title (may contain LaTeX formatting)
            
        Returns:
            Cleaned title in kebab-case
        """
        if not title:
            return ""
            
        # Remove LaTeX formatting
        cleaned = self._remove_latex_formatting(title)
        
        # Remove common stop words and keep meaningful words
        words = cleaned.lower().split()
        meaningful_words = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        # Take first few meaningful words
        selected_words = meaningful_words[:5]  # Limit to 5 words max
        
        if not selected_words:
            # Fall back to first few words if no meaningful words found
            selected_words = words[:3]
            
        title_text = " ".join(selected_words)
        
        # Convert to kebab-case
        kebab_title = self._to_kebab_case(title_text)
        
        # Truncate if too long
        if len(kebab_title) > self.MAX_COMPONENT_LENGTH:
            kebab_title = kebab_title[:self.MAX_COMPONENT_LENGTH].rstrip("-")
            
        return kebab_title

    def _extract_year(self, arxiv_id: str, metadata: dict[str, Any]) -> str:
        """Extract year from ArXiv ID or metadata.
        
        Args:
            arxiv_id: ArXiv paper ID
            metadata: Paper metadata
            
        Returns:
            4-digit year string
        """
        # Try to extract from ArXiv ID (YYMM.NNNN format)
        if re.match(r"^\d{4}\.\d+", arxiv_id):
            year_month = arxiv_id[:4]
            yy = int(year_month[:2])
            
            # Convert YY to full year (assuming papers from 1991-2099)
            if yy >= 91:  # 1991-1999
                full_year = 1900 + yy
            else:  # 2000-2099
                full_year = 2000 + yy
                
            return str(full_year)
            
        # Try to extract from metadata timestamps
        for date_field in ["processed_at", "saved_at", "submitted"]:
            if date_field in metadata:
                date_str = metadata[date_field]
                if isinstance(date_str, str) and len(date_str) >= 4:
                    try:
                        # Try to parse ISO format timestamp
                        parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        return str(parsed_date.year)
                    except ValueError:
                        # Try to extract year from string
                        year_match = re.search(r"(20\d{2})", date_str)
                        if year_match:
                            return year_match.group(1)
                            
        # Default to current year if nothing found
        return str(datetime.now().year)

    def _extract_field(self, categories: list[str]) -> str:
        """Extract field abbreviation from ArXiv categories.
        
        Args:
            categories: List of ArXiv categories
            
        Returns:
            Field abbreviation (e.g., "ai", "physics", "ml")
        """
        if not categories:
            return ""
            
        # Use the first category
        primary_category = categories[0].lower()
        
        # Direct mapping
        if primary_category in self.category_to_field:
            return self.category_to_field[primary_category]
            
        # Partial matching for categories with subcategories
        for category, field in self.category_to_field.items():
            if primary_category.startswith(category.split(".")[0]):
                return field
                
        # Extract main field from category format (e.g., "cs.ai" -> "cs")
        if "." in primary_category:
            main_field = primary_category.split(".")[0]
            return main_field
            
        # Return category as-is if no mapping found
        return primary_category[:10]  # Limit length

    def _remove_latex_formatting(self, text: str) -> str:
        """Remove LaTeX formatting from text.
        
        Args:
            text: Text that may contain LaTeX commands
            
        Returns:
            Clean text without LaTeX formatting
        """
        if not text:
            return ""
            
        # Remove common LaTeX commands
        text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)  # \command{content}
        text = re.sub(r"\\[a-zA-Z]+", "", text)  # \command
        text = re.sub(r"\{([^}]*)\}", r"\1", text)  # {content} -> content
        text = re.sub(r"[\{\}\\]", "", text)  # Remaining braces and backslashes
        
        # Remove special characters and normalize whitespace
        text = re.sub(r"[^\w\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()

    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case (lowercase with hyphens).
        
        Args:
            text: Input text
            
        Returns:
            Text in kebab-case format
        """
        if not text:
            return ""
            
        # Convert to lowercase and replace non-alphanumeric with hyphens
        kebab = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
        
        # Remove leading/trailing hyphens and consecutive hyphens
        kebab = re.sub(r"^-+|-+$", "", kebab)
        kebab = re.sub(r"-+", "-", kebab)
        
        return kebab

    def _normalize_string(self, text: str) -> str:
        """Normalize string for safe filename usage (alias for _to_kebab_case).
        
        Args:
            text: Input text
            
        Returns:
            Normalized text suitable for filenames
        """
        return self._to_kebab_case(text)

    def _truncate_filename(self, base_filename: str, extension: str) -> str:
        """Truncate filename to fit within length limits.
        
        Args:
            base_filename: Base filename without extension
            extension: File extension
            
        Returns:
            Truncated filename with extension
        """
        max_base_length = self.MAX_FILENAME_LENGTH - len(extension) - 1  # -1 for dot
        
        if len(base_filename) <= max_base_length:
            return f"{base_filename}.{extension}"
            
        # Truncate and remove trailing hyphen if any
        truncated = base_filename[:max_base_length].rstrip("-")
        return f"{truncated}.{extension}"

    def generate_directory_name(self, arxiv_id: str, metadata: dict[str, Any]) -> str:
        """Generate directory name for organizing papers.
        
        Args:
            arxiv_id: ArXiv paper ID
            metadata: Paper metadata
            
        Returns:
            Directory name (still uses arxiv_id for compatibility)
        """
        # For now, keep using arxiv_id for directory names to maintain
        # compatibility with existing code that expects this structure
        return arxiv_id

    def generate_paper_directory_name(self, arxiv_id: str, metadata: dict[str, Any]) -> str:
        """Generate human-readable paper directory name from metadata.
        
        Args:
            arxiv_id: ArXiv paper ID (used as fallback)
            metadata: Paper metadata containing title and authors
            
        Returns:
            Clean, human-readable directory name
        """
        if not metadata or "title" not in metadata:
            return arxiv_id
            
        title = metadata.get("title", "")
        authors = metadata.get("authors", [])
        
        # Clean and truncate title
        clean_title = self._clean_title_for_directory(title)
        
        # Get first author surname for prefix if available
        author_prefix = ""
        if authors and len(authors) > 0:
            first_author = authors[0] if isinstance(authors[0], str) else str(authors[0])
            # Extract last name (assuming "First Last" or "Last, First" format)
            if "," in first_author:
                author_prefix = first_author.split(",")[0].strip()
            else:
                author_prefix = first_author.split()[-1] if " " in first_author else first_author
            
            author_prefix = self._normalize_string(author_prefix)[:15]  # Limit length
        
        # Combine components
        if author_prefix and clean_title:
            directory_name = f"{author_prefix}-{clean_title}"
        elif clean_title:
            directory_name = clean_title
        else:
            directory_name = arxiv_id
            
        # Ensure uniqueness by appending arxiv_id year if available
        arxiv_year = arxiv_id.split(".")[0] if "." in arxiv_id else arxiv_id[:4]
        if arxiv_year.isdigit() and len(arxiv_year) == 4:
            directory_name = f"{directory_name}-{arxiv_year}"
        else:
            # Fallback: append first part of arxiv_id
            directory_name = f"{directory_name}-{arxiv_id.split('.')[0] if '.' in arxiv_id else arxiv_id[:8]}"
            
        # Final cleanup and length limit
        directory_name = self._normalize_string(directory_name)
        return directory_name[:self.MAX_FILENAME_LENGTH].rstrip("-")
    
    def _clean_title_for_directory(self, title: str) -> str:
        """Clean title for use in directory name.
        
        Args:
            title: Paper title
            
        Returns:
            Clean, truncated title suitable for directory name
        """
        # Remove common prefixes and suffixes
        title = re.sub(r"^(a|an|the)\s+", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+(a|an|the)\s+", " ", title, flags=re.IGNORECASE)
        
        # Normalize and clean
        title = self._normalize_string(title)
        
        # Remove stop words and truncate
        words = title.split("-")
        filtered_words = []
        total_length = 0
        
        for word in words:
            if word.lower() not in self.stop_words and len(word) > 1:
                if total_length + len(word) + 1 <= 50:  # Reserve space for author and year
                    filtered_words.append(word)
                    total_length += len(word) + 1
                else:
                    break
                    
        return "-".join(filtered_words) if filtered_words else title[:30]