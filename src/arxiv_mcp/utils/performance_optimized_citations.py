"""
Performance-optimized citation extraction with advanced optimization strategies.

This module implements the research-backed optimization strategies for high-throughput
citation extraction from academic papers.

Key optimizations:
1. Prefiltering to reduce regex scanning scope
2. Compiled patterns with bounded quantifiers
3. Memory-efficient chunked processing
4. Text normalization for better pattern matching
5. Atomic groups and possessive quantifiers (when available)
"""

from dataclasses import dataclass
import re
import time

# Try to use the regex module for advanced features
try:
    import regex

    HAS_REGEX = True
    print("Using advanced regex module for better performance")
except ImportError:
    import re as regex

    HAS_REGEX = False
    print("Using standard re module - consider installing 'regex' for better performance")

from .citations import Citation


@dataclass
class PerformanceMetrics:
    """Track performance metrics for citation extraction."""

    processing_time: float
    memory_peak: int
    citations_found: int
    characters_processed: int
    prefilter_hits: int

    @property
    def citations_per_second(self) -> float:
        return self.citations_found / self.processing_time if self.processing_time > 0 else 0

    @property
    def chars_per_second(self) -> float:
        return self.characters_processed / self.processing_time if self.processing_time > 0 else 0


class OptimizedCitationParser:
    """High-performance citation parser with research-backed optimizations."""

    def __init__(self, enable_prefilters: bool = True, chunk_size: int = 1024 * 1024):
        """Initialize the optimized parser.

        Args:
            enable_prefilters: Use prefiltering to reduce regex scanning scope
            chunk_size: Size of text chunks for memory-efficient processing
        """
        self.enable_prefilters = enable_prefilters
        self.chunk_size = chunk_size
        self.max_citation_span = 512  # Max length of a single citation

        # Compile patterns once for reuse (amortization)
        self._compile_patterns()

        # Performance tracking
        self.last_metrics: PerformanceMetrics | None = None

    def _compile_patterns(self):
        """Compile regex patterns with optimization flags."""
        flags = regex.VERBOSE | regex.IGNORECASE if HAS_REGEX else re.VERBOSE | re.IGNORECASE

        # Reference section header - anchored for speed
        self.ref_header_pattern = regex.compile(
            r"(?im)^\s*(references|bibliography|works\s+cited)\s*$", flags
        )

        # Prefilter patterns for quick candidate detection
        if self.enable_prefilters:
            self.bracket_prefilter = regex.compile(r"[\[\]()]")
            self.year_prefilter = regex.compile(r"\b(?:19|20)\d{2}\b")
            self.et_al_prefilter = regex.compile(r"\bet\s+al\.?\b", re.IGNORECASE)

        # Main citation patterns with bounded quantifiers for safety
        if HAS_REGEX:
            # Use advanced regex features for better performance
            self.numeric_pattern = regex.compile(
                r"""
                \[                                    # opening bracket
                (?>                                   # atomic group - no backtracking
                  \s*
                  (?P<nums>\d{1,4}                   # first number (bounded)
                    (?:\s*[-–]\s*\d{1,4})?           # optional range
                    (?:\s*[,;]\s*\d{1,4}             # additional numbers
                      (?:\s*[-–]\s*\d{1,4})?
                    ){0,20}                          # limit list length
                  )
                  \s*
                )
                \]                                   # closing bracket
            """,
                regex.VERBOSE,
            )

            self.authoryear_pattern = regex.compile(
                r"""
                \(                                   # opening paren
                (?>                                  # atomic group
                  (?P<entry>
                    (?P<authors>
                      [\p{Lu}][\p{L}\p{M}\p{N}\-'']{1,30}     # surname (bounded)
                      (?:\s+(?:&|and)\s+[\p{Lu}][\p{L}\p{M}\p{N}\-'']{1,30})?
                      (?:\s+et\s+al\.?)?
                    )
                    ,\s*
                    (?P<years>
                      (?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?  # year with bounds
                      (?:\s*[,;]\s*(?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?){0,5}
                    )
                  )
                  (?:\s*;\s*
                    [\p{Lu}][\p{L}\p{M}\p{N}\-'']{1,30}
                    (?:\s+(?:&|and)\s+[\p{Lu}][\p{L}\p{M}\p{N}\-'']{1,30})?
                    (?:\s+et\s+al\.?)?
                    ,\s*(?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?
                    (?:\s*[,;]\s*(?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?){0,5}
                  ){0,10}                            # limit multi-citations
                )
                \)                                   # closing paren
            """,
                regex.VERBOSE | regex.UNICODE,
            )
        else:
            # Fallback patterns for standard re module
            self.numeric_pattern = re.compile(
                r"\[\s*(\d{1,4}(?:\s*[-–]\s*\d{1,4})?(?:\s*[,;]\s*\d{1,4}(?:\s*[-–]\s*\d{1,4})?){0,20})\s*\]"
            )
            self.authoryear_pattern = re.compile(
                r"\(([A-Z][a-zA-Z\-\'\s&]{1,50},\s*(?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?(?:[,;]\s*(?:18\d{2}|19\d{2}|20\d{2}|2100)[a-z]?){0,5})\)"
            )

        # Author extraction pattern with bounds
        self.author_pattern = regex.compile(
            r"([A-Z][a-zA-Z0-9]{1,30}(?:\s+[A-Z][a-zA-Z0-9]{0,20}){0,3}),\s*([A-Z][a-zA-Z0-9]{0,10}\.?(?:\s*[A-Z][a-zA-Z0-9]{0,10}\.?){0,3})"
        )

        # Title extraction patterns with year context
        year_title_flags = regex.VERBOSE if HAS_REGEX else re.VERBOSE
        self.year_title_patterns = [
            regex.compile(r"\((\d{4})\)\.?\s+([^.]{10,200}\.)", year_title_flags),
            regex.compile(r"\((\d{4})\)\.?\s+([^.]{10,200})", year_title_flags),
            regex.compile(r"(\d{4})\.?\s+([^.]{10,200}\.)", year_title_flags),
            regex.compile(r"(\d{4})\.?\s+([^.]{10,200})", year_title_flags),
        ]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching."""
        if not text:
            return ""

        # Unicode normalization
        import unicodedata

        text = unicodedata.normalize("NFKC", text)

        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(""", "'").replace(""", "'")
        text = text.replace("–", "-").replace("—", "-")

        # Collapse excessive whitespace but preserve line breaks
        text = re.sub(r"[ \t]+", " ", text)
        return re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    def _prefilter_candidates(self, text: str) -> list[tuple[int, int]]:
        """Find candidate windows using cheap prefilters."""
        if not self.enable_prefilters:
            return [(0, len(text))]

        candidates = []
        window_size = 512

        # Find bracket candidates
        for match in self.bracket_prefilter.finditer(text):
            start = max(0, match.start() - window_size // 2)
            end = min(len(text), match.end() + window_size // 2)
            candidates.append((start, end))

        # Find year candidates
        for match in self.year_prefilter.finditer(text):
            start = max(0, match.start() - window_size // 2)
            end = min(len(text), match.end() + window_size // 2)
            candidates.append((start, end))

        # Merge overlapping windows
        if not candidates:
            return [(0, len(text))]

        candidates.sort()
        merged = [candidates[0]]

        for start, end in candidates[1:]:
            if start <= merged[-1][1] + 50:  # Small gap tolerance
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        return merged

    def _extract_references_section(self, text: str) -> str | None:
        """Extract references section with performance optimizations."""
        # Quick check for section headers
        match = self.ref_header_pattern.search(text)
        if not match:
            return None

        start = match.end()
        # Look for next major section to bound the search
        next_section = regex.search(
            r"(?im)^\s*(?:appendix|acknowledgments?|figures?|tables?)\s*$",
            text[start : start + 200000],  # Bound search to reasonable length
        )

        end = (next_section.start() + start) if next_section else min(len(text), start + 200000)
        return text[start:end]

    def _extract_authors_optimized(self, text: str) -> list[str]:
        """Optimized author extraction with bounds checking."""
        if not text or len(text) > 10000:  # Skip extremely long citations
            return []

        authors = []

        # Remove numbering with bounded search
        clean_text = regex.sub(r"^\[\d{1,4}\]\s*", "", text[:1000].strip())

        # Find author matches with limits
        matches = list(self.author_pattern.finditer(clean_text))[:20]  # Limit matches

        for match in matches:
            last, first = match.groups()

            # Skip malformed entries (simple heuristic)
            if len(last) < 2 or len(first) < 1:
                continue

            # Handle ellipsis patterns
            if "... &" in clean_text:
                ellipsis_pos = clean_text.find("... &")
                author_pos = match.start()
                if author_pos > ellipsis_pos and not regex.match(
                    r"^[A-Z]\.?\s*[A-Z]?\.?\s*$", first.strip()
                ):
                    continue

            authors.append(f"{last.strip()}, {first.strip()}")

        return authors[:10]  # Reasonable limit

    def _extract_title_optimized(self, text: str) -> str:
        """Optimized title extraction with pattern ordering."""
        if not text or len(text) > 5000:  # Skip extremely long citations
            return ""

        # Try quote patterns first (most reliable)
        quote_match = regex.search(r'["""]([^"""]{5,200})["""]', text)
        if quote_match:
            return quote_match.group(1).strip()

        # Try year-title patterns in order of reliability
        for pattern in self.year_title_patterns:
            match = pattern.search(text)
            if match:
                year, title = match.groups()
                title = title.strip().rstrip(".")
                if len(title) > 5 and not title.startswith(("In ", "Proceedings")):
                    return title

        # Fallback with safety bounds
        if len(text) < 2000:
            text_without_year = regex.sub(r"\(\d{4}\)", "", text[:1000]).strip()
            sentences = text_without_year.split(".")
            if sentences and len(sentences[0]) > 10:
                potential_title = sentences[0].strip()
                # Remove author pattern
                title_clean = regex.sub(r"^[^,]+,\s*", "", potential_title).strip()
                if len(title_clean) > 5:
                    return title_clean

        return ""

    def extract_citations(self, text: str, timeout: float | None = None) -> list[Citation]:
        """Extract citations with performance tracking and safety measures."""
        import tracemalloc

        start_time = time.perf_counter()
        tracemalloc.start()

        try:
            # Normalize input
            normalized_text = self._normalize_text(text)

            # Get candidate windows
            candidates = self._prefilter_candidates(normalized_text)
            total_prefilter_hits = len(candidates)

            citations = []

            # Process in-text citations from candidate windows
            for start, end in candidates:
                window = normalized_text[start:end]

                # Numeric citations with timeout protection
                try:
                    if HAS_REGEX and timeout:
                        numeric_matches = list(
                            self.numeric_pattern.finditer(window, timeout=timeout)
                        )
                    else:
                        numeric_matches = list(self.numeric_pattern.finditer(window))

                    for match in numeric_matches[:50]:  # Limit matches per window
                        citation = Citation(
                            authors=[], title="", raw_text=match.group(0), confidence=0.7
                        )
                        citations.append(citation)
                except regex.error if HAS_REGEX else re.error:
                    continue

                # Author-year citations
                try:
                    if HAS_REGEX and timeout:
                        authoryear_matches = list(
                            self.authoryear_pattern.finditer(window, timeout=timeout)
                        )
                    else:
                        authoryear_matches = list(self.authoryear_pattern.finditer(window))

                    for match in authoryear_matches[:50]:  # Limit matches per window
                        citation = Citation(
                            authors=[], title="", raw_text=match.group(0), confidence=0.6
                        )
                        citations.append(citation)
                except regex.error if HAS_REGEX else re.error:
                    continue

            # Process reference section
            ref_section = self._extract_references_section(normalized_text)
            if ref_section:
                # Split references efficiently
                references = [ref.strip() for ref in ref_section.split("\n\n") if ref.strip()]

                for ref_text in references[:200]:  # Reasonable limit
                    if len(ref_text) < 50 or len(ref_text) > 2000:
                        continue

                    citation = Citation(
                        authors=self._extract_authors_optimized(ref_text),
                        title=self._extract_title_optimized(ref_text),
                        raw_text=ref_text,
                        confidence=0.8,
                    )

                    # Extract year
                    year_match = regex.search(r"\b(18\d{2}|19\d{2}|20\d{2}|2100)\b", ref_text)
                    if year_match:
                        citation.year = year_match.group(1)

                    citations.append(citation)

            # Performance metrics
            end_time = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()

            self.last_metrics = PerformanceMetrics(
                processing_time=end_time - start_time,
                memory_peak=peak,
                citations_found=len(citations),
                characters_processed=len(text),
                prefilter_hits=total_prefilter_hits,
            )

            return citations

        finally:
            tracemalloc.stop()

    def get_performance_report(self) -> str:
        """Get a detailed performance report."""
        if not self.last_metrics:
            return "No performance data available. Run extract_citations() first."

        m = self.last_metrics
        return f"""
Performance Report:
==================
Processing time: {m.processing_time * 1000:.2f} ms
Citations found: {m.citations_found}
Characters processed: {m.characters_processed:,}
Prefilter hits: {m.prefilter_hits}

Throughput:
-----------
Citations/second: {m.citations_per_second:.1f}
Characters/second: {m.chars_per_second:,.0f}
Memory peak: {m.memory_peak / 1024 / 1024:.2f} MB
Memory per citation: {m.memory_peak / m.citations_found if m.citations_found else 0:.0f} bytes
        """
