"""
Citation parsing and reference extraction for academic papers.

This module provides comprehensive citation parsing capabilities with support
for multiple citation formats (APA, MLA, IEEE, BibTeX) and reference extraction
from academic papers.
"""

from dataclasses import dataclass
from enum import Enum
import re
import warnings

from .logging import structured_logger
from .optional_deps import safe_import_nltk

# Safe imports with fallbacks
try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None
    warnings.warn(
        "BeautifulSoup4 not available. HTML citation parsing will be limited.",
        UserWarning,
    )

# Get NLTK safely - don't fail on import issues
try:
    nltk = safe_import_nltk()
    NLTK_AVAILABLE = nltk is not None
except Exception:
    # If there are any issues with NLTK, fall back gracefully
    nltk = None
    NLTK_AVAILABLE = False
    warnings.warn(
        "NLTK not available due to import issues. Using basic text processing.",
        UserWarning,
    )


class CitationFormat(Enum):
    """Supported citation formats."""

    BIBTEX = "bibtex"
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    NATURE = "nature"


@dataclass
class Citation:
    """Represents a parsed citation."""

    authors: list[str]
    title: str
    journal: str | None = None
    year: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    raw_text: str = ""
    confidence: float = 0.0


class CitationParser:
    """Intelligent citation parser with multiple format support."""

    def __init__(self):
        self.logger = structured_logger()

        # Citation patterns for different formats
        self.patterns = {
            "arxiv_id": r"arXiv:(\d{4}\.\d{4,5})(v\d+)?",
            "doi": r"doi:?\s*(?:https?://(?:dx\.)?doi\.org/)?(10\.\d+/[^\s]+)",
            "url": r"https?://[^\s]+",
            "year": r"\b(19|20)\d{2}\b",
            "pages": r"(?:pp?\.)?\s*(\d+(?:[-–]\d+)?)",
            "volume": r"(?:vol\.?\s*|volume\s*)(\d+)",
            "issue": r"(?:no\.?\s*|issue\s*)(\d+)",
        }

        # Common citation separators
        self.separators = [
            r"\.\s+",  # Period followed by space
            r",\s+",  # Comma followed by space
            r";\s+",  # Semicolon followed by space
            r"\n\s*",  # Newline
        ]

        if NLTK_AVAILABLE:
            try:
                # Download required NLTK data if not present
                import nltk.data

                nltk.data.find("tokenizers/punkt")
            except LookupError:
                self.logger.info("Downloading NLTK punkt tokenizer data...")
                try:
                    nltk.download("punkt", quiet=True)
                except Exception:
                    self.logger.warning("Failed to download NLTK data")

    def extract_citations_from_text(self, text: str) -> list[Citation]:
        """Extract citations from academic paper text."""
        if not text or not isinstance(text, str):
            return []

        citations = []

        # Look for references section first
        ref_text = self._extract_references_section(text)

        if ref_text:
            # If we have a formal references section, extract from it
            citation_strings = self._split_citations(ref_text)

            for i, citation_str in enumerate(citation_strings):
                citation = self._parse_single_citation(citation_str)
                if citation and (citation.authors or citation.title):
                    citation.confidence = self._calculate_confidence(citation)
                    citations.append(citation)

            # For inline citations, only extract from text OUTSIDE the references section
            # Find the position of the references section
            ref_patterns = [
                r"\n\s*(?:REFERENCES?|BIBLIOGRAPHY|WORKS?\s+CITED)\s*\n",
                r"\n\s*\d+\.?\s*(?:References?|Bibliography)\s*\n",
                r"\n\s*(?:\[\d+\]|\d+\.)\s*[A-Z]",  # Numbered references
            ]

            main_text = text
            for pattern in ref_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    main_text = text[: match.start()]  # Text before references section
                    break

            # Extract inline citations only from main text (not references section)
            inline_citations = self._extract_inline_citations(main_text)
            citations.extend(inline_citations)
        else:
            # No formal references section found, extract inline citations from entire text
            inline_citations = self._extract_inline_citations(text)
            citations.extend(inline_citations)

        self.logger.info(f"Extracted {len(citations)} citations from text")
        return citations

    def extract_citations(self, text: str) -> list[Citation]:
        """
        Alias for extract_citations_from_text for backward compatibility.

        Args:
            text: Input text to analyze

        Returns:
            List of Citation objects found in the text
        """
        return self.extract_citations_from_text(text)

    def _extract_inline_citations(self, text: str) -> list[Citation]:
        """Extract inline citations like (Author et al., Year) from text."""
        citations = []

        # Pattern for inline citations: (Author et al., Year) or (Author & Author, Year)
        inline_patterns = [
            r"\(([A-Z][a-zA-Z\s]+(?:\s+et\s+al\.?)?),?\s*(\d{4})\)",  # (LeCun et al., 2015)
            # (Author & Author, 2015)
            r"\(([A-Z][a-zA-Z\s]+)\s*&\s*([A-Z][a-zA-Z\s]+),?\s*(\d{4})\)",
            r"([A-Z][a-zA-Z\s]+(?:\s+et\s+al\.?)?)\s*\((\d{4})\)",  # Author et al. (2015)
        ]

        for pattern in inline_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:  # Single author or et al.
                    author_part, year = match
                    citation = Citation(
                        authors=[author_part.strip()],
                        title="",
                        year=year,
                        raw_text=f"({author_part.strip()}, {year})",
                    )
                elif len(match) == 3:  # Two authors
                    author1, author2, year = match
                    citation = Citation(
                        authors=[author1.strip(), author2.strip()],
                        title="",
                        year=year,
                        raw_text=f"({author1.strip()} & {author2.strip()}, {year})",
                    )
                else:
                    continue

                citation.confidence = 0.7  # Medium confidence for inline citations
                citations.append(citation)

        return citations

    def _extract_references_section(self, text: str) -> str | None:
        """Extract the references/bibliography section from paper text."""
        if not text or not isinstance(text, str):
            return None

        # Common reference section headers
        ref_patterns = [
            r"\n\s*(?:REFERENCES?|BIBLIOGRAPHY|WORKS?\s+CITED)\s*\n",
            r"\n\s*\d+\.?\s*(?:References?|Bibliography)\s*\n",
        ]

        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Extract from this point to end or next major section
                start = match.end()
                # Look for next major section
                next_section = re.search(
                    r"\n\s*(?:APPENDIX|ACKNOWLEDGMENTS?|FIGURES?|TABLES?)\s*\n",
                    text[start:],
                    re.IGNORECASE,
                )
                end = next_section.start() + start if next_section else len(text)
                return text[start:end]

        # If no formal header found, look for numbered references pattern
        # but be more careful about the extraction
        numbered_pattern = r"\n\s*(?:\[\d+\]|\d+\.)\s*[A-Z]"
        match = re.search(numbered_pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Start from the beginning of the line that contains the numbered reference
            line_start = text.rfind("\n", 0, match.start()) + 1
            start = line_start
            # Look for next major section
            next_section = re.search(
                r"\n\s*(?:APPENDIX|ACKNOWLEDGMENTS?|FIGURES?|TABLES?)\s*\n",
                text[start:],
                re.IGNORECASE,
            )
            end = next_section.start() + start if next_section else len(text)
            return text[start:end]

        return None

    def _split_citations(self, text: str) -> list[str]:
        """Split reference text into individual citations."""
        citations = []

        # Try numbered format first [1], [2], etc. - enhanced boundary detection
        # Split text by numbered citation markers, then reconstruct
        if re.search(r"\[\d+\]", text):
            # Find all numbered citation positions
            citation_positions = []
            for match in re.finditer(r"\[\d+\]", text):
                citation_positions.append((match.start(), match.end(), match.group()))

            if citation_positions:
                citations_raw = []

                for i, (start, end, marker) in enumerate(citation_positions):
                    # Find the end position for this citation
                    if i + 1 < len(citation_positions):
                        next_start = citation_positions[i + 1][0]
                        citation_end = next_start
                    else:
                        citation_end = len(text)

                    # Extract citation content including the marker
                    citation_content = text[start:citation_end].strip()
                    if citation_content:
                        citations_raw.append(citation_content)

                # Filter and clean citations
                cleaned_citations = []
                for citation_text in citations_raw:
                    if not citation_text:
                        continue

                    # Clean up citation by removing lines that don't look like citation content
                    citation_lines = citation_text.split("\n")
                    cleaned_lines = []

                    for line in citation_lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Stop if we hit text that clearly isn't part of the citation
                        if self._is_non_citation_text(line):
                            break

                        cleaned_lines.append(line)

                    if cleaned_lines:
                        cleaned_citations.append(" ".join(cleaned_lines))

                if cleaned_citations:
                    return cleaned_citations

        # Try parenthetical numbering (1), (2), etc.
        paren_pattern = r"\((\d+)\)\s*([^(]*?)(?=\(\d+\)|$)"
        paren_matches = re.findall(paren_pattern, text, re.DOTALL)

        if paren_matches:
            return [match[1].strip() for match in paren_matches]

        # Fall back to sentence-based splitting
        if NLTK_AVAILABLE:
            sentences = nltk.sent_tokenize(text)
            # Group sentences that look like citations
            current_citation = []
            for sentence in sentences:
                if self._looks_like_citation_start(sentence):
                    if current_citation:
                        citations.append(" ".join(current_citation))
                    current_citation = [sentence]
                else:
                    current_citation.append(sentence)

            if current_citation:
                citations.append(" ".join(current_citation))
        else:
            # Simple split on double newlines
            citations = [c.strip() for c in text.split("\n\n") if c.strip()]

        return citations

    def _looks_like_citation_start(self, sentence: str) -> bool:
        """Check if sentence looks like the start of a citation."""
        # Starts with author name pattern
        author_pattern = r"^[A-Z][a-z]+,?\s+[A-Z]"
        if re.match(author_pattern, sentence.strip()):
            return True

        # Contains year in parentheses
        year_pattern = r"\((?:19|20)\d{2}\)"
        if re.search(year_pattern, sentence):
            return True

        return False

    def _is_non_citation_text(self, line: str) -> bool:
        """Determine if a line of text is likely not part of a citation."""
        line = line.strip()
        if not line:
            return False

        # Lines that start with common non-citation phrases
        non_citation_starters = [
            "this is",
            "that is",
            "these are",
            "those are",
            "another",
            "the following",
            "as shown",
            "for example",
            "note that",
            "it should be",
            "we can see",
            "in addition",
            "furthermore",
            "moreover",
            "however",
            "therefore",
            "thus",
            "hence",
            "consequently",
        ]

        line_lower = line.lower()
        for starter in non_citation_starters:
            if line_lower.startswith(starter):
                return True

        # Lines that don't contain typical citation elements
        has_year = bool(re.search(r"\b(19|20)\d{2}\b", line))
        has_author_pattern = bool(re.search(r"[A-Z][a-z]+,?\s+[A-Z]", line))
        has_title_pattern = bool(re.search(r"[A-Z][a-z].*[a-z]", line))
        has_journal_pattern = bool(
            re.search(
                r"Journal|Review|Letters|Transactions|Conference|Proceedings", line, re.IGNORECASE
            )
        )

        # If line has none of the typical citation elements, it's likely not a citation
        citation_indicators = sum(
            [has_year, has_author_pattern, has_title_pattern, has_journal_pattern]
        )

        # Lines with too few citation indicators are likely non-citation text
        # BUT be less aggressive - require very clear non-citation signals
        # Don't filter out lines that could be title continuations
        if citation_indicators == 0 and len(line) > 20:
            # Additional checks for title-like content
            # Allow lines that contain common title words
            title_words = [
                "research",
                "study",
                "analysis",
                "method",
                "approach",
                "system",
                "algorithm",
                "model",
                "technique",
                "framework",
                "theory",
                "design",
                "development",
                "investigation",
                "experiment",
                "results",
                "findings",
                "application",
                "implementation",
                "evaluation",
                "assessment",
                "review",
                "survey",
                "comprehensive",
                "novel",
                "innovative",
                "advanced",
                "improved",
                "effective",
                "efficient",
                "optimal",
                "robust",
                "scalable",
                "automated",
                "machine",
                "learning",
                "neural",
                "network",
                "data",
                "artificial",
                "intelligence",
                "computer",
                "software",
                "hardware",
                "technology",
                "methodology",
                "technical",
                "scientific",
                "academic",
                "detailed",
                "descriptions",
                "terms",
            ]

            line_words = line_lower.split()
            has_title_words = any(word in title_words for word in line_words)

            # Don't filter if line contains title-like words
            if has_title_words:
                return False

            # Filter out if line is very long and has no citation or title indicators
            return len(line) > 50

        return False

    def _parse_single_citation(self, citation_str: str) -> Citation | None:
        """Parse a single citation string."""
        if not citation_str.strip():
            return None

        citation = Citation(authors=[], title="", raw_text=citation_str.strip())

        # Extract structured information
        citation.authors = self._extract_authors(citation_str)
        citation.title = self._extract_title(citation_str)
        citation.year = self._extract_year(citation_str)
        citation.journal = self._extract_journal(citation_str)
        citation.doi = self._extract_doi(citation_str)
        citation.arxiv_id = self._extract_arxiv_id(citation_str)
        citation.url = self._extract_url(citation_str)
        citation.pages = self._extract_pages(citation_str)
        citation.volume = self._extract_volume(citation_str)
        citation.issue = self._extract_issue(citation_str)

        return citation

    def _extract_authors(self, text: str) -> list[str]:
        """Extract author names from citation text."""
        authors = []

        # Normalize whitespace for better parsing
        text = re.sub(r"\s+", " ", text.strip())

        # First, try to extract the author section (everything before the year)
        year_match = re.search(r"\((?:19|20)\d{2}\)", text)
        if year_match:
            author_section = text[: year_match.start()].strip()
        else:
            # If no year found, take first part (heuristic)
            author_section = text.split(".")[0] if "." in text else text

        # Remove citation numbering at start
        author_section = re.sub(r"^\[\d+\]\s*", "", author_section)

        # Pattern for comma-separated authors with initials
        # Handles: "Author0, A., Author1, B., Author2, C." etc.
        comma_sep_pattern = r"([\w\u00C0-\u017F\u4e00-\u9fff']+),\s*([\w\u00C0-\u017F\u4e00-\u9fff]\.?(?:\s*[\w\u00C0-\u017F\u4e00-\u9fff]\.?)*)"
        comma_matches = re.findall(comma_sep_pattern, author_section, re.UNICODE)

        if comma_matches:
            for last, first in comma_matches:
                # Preserve original "Last, First" format when found in comma-separated style
                author = f"{last.strip()}, {first.strip()}"
                authors.append(author)
        else:
            # Fallback: Pattern for "LastName, FirstName" format - enhanced for Unicode names
            # Supports ASCII, Latin extended, Chinese, and other Unicode letters
            author_pattern = (
                r"([\w\u00C0-\u017F\u4e00-\u9fff']+(?:\s+[\w\u00C0-\u017F\u4e00-\u9fff]\.?)*),?"
                r"\s+([\w\u00C0-\u017F\u4e00-\u9fff]\.?(?:\s+[\w\u00C0-\u017F\u4e00-\u9fff]\.?)*"
                r"|[\w\u00C0-\u017F\u4e00-\u9fff']+)"
            )
            matches = re.findall(author_pattern, author_section, re.UNICODE)

            for last, first in matches:
                # Preserve original "Last, First" format when structured this way
                author = f"{last.strip()}, {first.strip()}"
                authors.append(author)

        # If still no structured authors found, try simple pattern
        if not authors:
            # Look for "and" separated names - enhanced for Unicode
            and_pattern = (
                r"([\w\u00C0-\u017F\u4e00-\u9fff']+(?:\s+[\w\u00C0-\u017F\u4e00-\u9fff']+)*)"
                r"\s+and\s+"
                r"([\w\u00C0-\u017F\u4e00-\u9fff']+(?:\s+[\w\u00C0-\u017F\u4e00-\u9fff']+)*)"
            )
            and_matches = re.findall(and_pattern, author_section, re.UNICODE)
            authors.extend([match[0] for match in and_matches])
            authors.extend([match[1] for match in and_matches])

        return authors[:10]  # Limit to reasonable number

    def _extract_title(self, text: str) -> str:
        """Extract paper title from citation text."""
        # Normalize whitespace and line breaks
        text = re.sub(r"\s+", " ", text.strip())

        # Title often in quotes or after author/year
        quote_pattern = r'["""]([^"""]+)["""]'
        quote_match = re.search(quote_pattern, text)
        if quote_match:
            return quote_match.group(1).strip()

        # Find the year marker to locate title
        year_match = re.search(r"\((?:19|20)\d{2}\)", text)
        if year_match:
            # Extract text after (year).
            title_start = year_match.end()
            title_text = text[title_start:].strip()

            # Remove leading period and whitespace
            title_text = re.sub(r"^\.\s*", "", title_text)

            # Extract title until next major section (journal, venue, etc.)
            title_patterns = [
                # Stop at journal/venue indicators - but capture everything until the period before them
                r"^(.*?)\.?\s*(?:In\s|Advances\s|[A-Z][\w\s&]*(?:Journal|Review|Report|Letters|Transactions|Conference|Proceedings)|Nature|Science|Cell)",
                # Stop at volume/page indicators
                r"^([^.]+?)\.?\s*(?:\d+\(\d+\)|vol\.?\s*\d+|pp?\.?\s*\d+)",
                # Fallback: take everything until first period (if reasonable length)
                r"^([^.]{10,}?)\.(?:\s|$)",
                # Last resort: take first substantial chunk
                r"^([^.]{5,}?)(?:\.|$)",
            ]

            for pattern in title_patterns:
                match = re.search(pattern, title_text, re.IGNORECASE | re.UNICODE)
                if match:
                    title = match.group(1).strip()
                    # Validate title length and content
                    if 3 <= len(title) <= 500 and not re.match(r"^Author\d+", title):
                        return title

            # If patterns failed, take text up to first reasonable break
            words = title_text.split()
            if words:
                # Take words until we hit something that looks like a journal/venue
                title_words = []
                for word in words:
                    if re.match(
                        r"^(Journal|Review|Letters|Transactions|Conference|Proceedings|Nature|Science|Cell)$",
                        word,
                        re.IGNORECASE,
                    ):
                        break
                    title_words.append(word)

                if title_words:
                    potential_title = " ".join(title_words).rstrip(".,;:")
                    if 3 <= len(potential_title) <= 500:
                        return potential_title

        # Fallback: Look for patterns without year dependency
        # This should rarely be used with the improved year-based extraction above
        parts = text.split(".")
        if len(parts) >= 2:
            for i in range(1, min(len(parts), 4)):  # Check first few parts
                potential_title = parts[i].strip()
                # Remove leading punctuation and whitespace
                potential_title = re.sub(r"^[\s.:;,]+", "", potential_title)
                # Skip parts that look like author names
                if (
                    potential_title
                    and not re.match(r"^Author\d+", potential_title)
                    and 5 <= len(potential_title) <= 200
                ):
                    return potential_title

        return ""

    def _extract_year(self, text: str) -> str | None:
        """Extract publication year."""
        match = re.search(self.patterns["year"], text)
        return match.group(0) if match else None

    def _extract_journal(self, text: str) -> str | None:
        """Extract journal name."""
        # Journal often after title, before volume/pages
        journal_patterns = [
            r"(?:In\s+)?([A-Z][^,.\d]*?)(?:\s*,?\s*(?:vol\.?|volume|\d+))",
            r"(?:In\s+)?([A-Z][a-zA-Z\s&]+?)(?:\s*\d+)",
        ]

        for pattern in journal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                journal = match.group(1).strip()
                if len(journal) > 3 and not re.match(r"^\d+$", journal):
                    return journal

        return None

    def _extract_doi(self, text: str) -> str | None:
        """Extract DOI."""
        match = re.search(self.patterns["doi"], text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_arxiv_id(self, text: str) -> str | None:
        """Extract ArXiv ID."""
        match = re.search(self.patterns["arxiv_id"], text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_url(self, text: str) -> str | None:
        """Extract URL."""
        match = re.search(self.patterns["url"], text)
        return match.group(0) if match else None

    def _extract_pages(self, text: str) -> str | None:
        """Extract page numbers."""
        match = re.search(self.patterns["pages"], text)
        return match.group(1) if match else None

    def _extract_volume(self, text: str) -> str | None:
        """Extract volume number."""
        match = re.search(self.patterns["volume"], text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_issue(self, text: str) -> str | None:
        """Extract issue number."""
        match = re.search(self.patterns["issue"], text, re.IGNORECASE)
        return match.group(1) if match else None

    def _calculate_confidence(self, citation: Citation) -> float:
        """Calculate confidence score for parsed citation."""
        score = 0.0

        # Base score for having content
        if citation.authors:
            score += 0.3
        if citation.title:
            score += 0.3
        if citation.year:
            score += 0.2
        if citation.journal:
            score += 0.1
        if citation.doi or citation.arxiv_id:
            score += 0.1

        return min(score, 1.0)

    def format_citation(self, citation: Citation, format_type: CitationFormat) -> str:
        """Format citation in specified style."""
        if format_type == CitationFormat.BIBTEX:
            return self._format_bibtex(citation)
        if format_type == CitationFormat.APA:
            return self._format_apa(citation)
        if format_type == CitationFormat.MLA:
            return self._format_mla(citation)
        if format_type == CitationFormat.IEEE:
            return self._format_ieee(citation)
        return citation.raw_text

    def _format_bibtex(self, citation: Citation) -> str:
        """Format as BibTeX entry."""
        entry_type = "article" if citation.journal else "misc"
        key = self._generate_bibtex_key(citation)

        lines = [f"@{entry_type}{{{key},"]

        if citation.title:
            lines.append(f"  title = {{{citation.title}}},")
        if citation.authors:
            authors_str = " and ".join(citation.authors)
            lines.append(f"  author = {{{authors_str}}},")
        if citation.journal:
            lines.append(f"  journal = {{{citation.journal}}},")
        if citation.year:
            lines.append(f"  year = {{{citation.year}}},")
        if citation.volume:
            lines.append(f"  volume = {{{citation.volume}}},")
        if citation.issue:
            lines.append(f"  number = {{{citation.issue}}},")
        if citation.pages:
            lines.append(f"  pages = {{{citation.pages}}},")
        if citation.doi:
            lines.append(f"  doi = {{{citation.doi}}},")
        if citation.arxiv_id:
            lines.append(f"  note = {{arXiv:{citation.arxiv_id}}},")

        lines.append("}")
        return "\n".join(lines)

    def _format_apa(self, citation: Citation) -> str:
        """Format in APA style."""
        parts = []

        if citation.authors:
            # APA author format: Last, F. M.
            apa_authors = []
            for author in citation.authors:
                name_parts = author.split()
                if len(name_parts) >= 2:
                    last_name = name_parts[-1]
                    initials = " ".join([n[0] + "." for n in name_parts[:-1]])
                    apa_authors.append(f"{last_name}, {initials}")

            if len(apa_authors) > 1:
                authors_str = ", ".join(apa_authors[:-1]) + f", & {apa_authors[-1]}"
            else:
                authors_str = apa_authors[0] if apa_authors else ""
            parts.append(authors_str)

        if citation.year:
            parts.append(f"({citation.year})")

        if citation.title:
            parts.append(f"{citation.title}.")

        if citation.journal:
            journal_part = f"*{citation.journal}*"
            if citation.volume:
                journal_part += f", {citation.volume}"
            if citation.issue:
                journal_part += f"({citation.issue})"
            if citation.pages:
                journal_part += f", {citation.pages}"
            parts.append(journal_part + ".")

        return " ".join(parts)

    def _format_mla(self, citation: Citation) -> str:
        """Format in MLA style."""
        parts = []

        if citation.authors:
            # MLA format: Last, First
            primary_author = citation.authors[0]
            name_parts = primary_author.split()
            if len(name_parts) >= 2:
                mla_author = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
                parts.append(mla_author + ".")

        if citation.title:
            parts.append(f'"{citation.title}."')

        if citation.journal:
            parts.append(f"*{citation.journal}*,")

        if citation.volume:
            parts.append(f"vol. {citation.volume},")

        if citation.issue:
            parts.append(f"no. {citation.issue},")

        if citation.year:
            parts.append(f"{citation.year},")

        if citation.pages:
            parts.append(f"pp. {citation.pages}.")

        return " ".join(parts)

    def _format_ieee(self, citation: Citation) -> str:
        """Format in IEEE style."""
        parts = []

        if citation.authors:
            # IEEE format: F. Last
            ieee_authors = []
            for author in citation.authors:
                name_parts = author.split()
                if len(name_parts) >= 2:
                    first_initials = " ".join([n[0] + "." for n in name_parts[:-1]])
                    last_name = name_parts[-1]
                    ieee_authors.append(f"{first_initials} {last_name}")
            parts.append(", ".join(ieee_authors) + ",")

        if citation.title:
            parts.append(f'"{citation.title},"')

        if citation.journal:
            journal_part = f"*{citation.journal}*"
            if citation.volume:
                journal_part += f", vol. {citation.volume}"
            if citation.issue:
                journal_part += f", no. {citation.issue}"
            if citation.pages:
                journal_part += f", pp. {citation.pages}"
            if citation.year:
                journal_part += f", {citation.year}"
            parts.append(journal_part + ".")

        return " ".join(parts)

    def _generate_bibtex_key(self, citation: Citation) -> str:
        """Generate BibTeX key from citation data."""
        key_parts = []

        if citation.authors:
            first_author = citation.authors[0].split()[-1].lower()  # Last name
            key_parts.append(first_author)

        if citation.year:
            key_parts.append(citation.year)

        if citation.title:
            # Take first significant word from title
            title_words = citation.title.lower().split()
            significant_words = [
                w for w in title_words if len(w) > 3 and w not in ["the", "and", "for", "with"]
            ]
            if significant_words:
                key_parts.append(significant_words[0])

        return "".join(key_parts) if key_parts else "unknown"


def extract_citations_from_pdf_text(pdf_text: str) -> list[Citation]:
    """Convenience function to extract citations from PDF text."""
    parser = CitationParser()
    return parser.extract_citations_from_text(pdf_text)


def format_citations_as_bibliography(
    citations: list[Citation], format_type: CitationFormat = CitationFormat.APA
) -> str:
    """Format multiple citations as a bibliography."""
    parser = CitationParser()
    formatted_citations = []

    for citation in citations:
        formatted = parser.format_citation(citation, format_type)
        if formatted:
            formatted_citations.append(formatted)

    return "\n\n".join(formatted_citations)
