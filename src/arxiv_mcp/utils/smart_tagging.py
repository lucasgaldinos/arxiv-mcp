#!/usr/bin/env python3
"""
Smart Tagging System for ArXiv MCP

This module provides automatic keyword extraction and tagging capabilities
for research papers, leveraging NLP techniques and domain-specific knowledge.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import json
import sqlite3
from datetime import datetime

# Optional NLTK imports
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import PorterStemmer
    from nltk.chunk import ne_chunk
    from nltk.tag import pos_tag

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class Tag:
    """Represents a smart tag with metadata."""

    term: str
    category: str
    confidence: float
    frequency: int = 0
    contexts: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)


@dataclass
class TaggingResult:
    """Result of smart tagging operation."""

    paper_id: str
    tags: List[Tag]
    categories: Dict[str, List[Tag]]
    confidence_score: float
    processing_time: float
    method_used: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SmartTagger:
    """
    Advanced tagging system for automatic keyword extraction and categorization.

    Features:
    - Domain-specific keyword extraction
    - Multi-level categorization
    - Confidence scoring
    - Tag persistence and analytics
    - Contextual analysis
    """

    # Academic field mapping
    FIELD_KEYWORDS = {
        "machine_learning": {
            "neural",
            "network",
            "deep",
            "learning",
            "classification",
            "regression",
            "clustering",
            "supervised",
            "unsupervised",
            "reinforcement",
            "gradient",
            "optimization",
            "feature",
            "training",
            "validation",
            "accuracy",
            "precision",
            "recall",
        },
        "computer_vision": {
            "image",
            "vision",
            "detection",
            "recognition",
            "segmentation",
            "convolution",
            "cnn",
            "object",
            "face",
            "tracking",
            "opencv",
            "pixels",
            "filtering",
            "enhancement",
            "morphology",
        },
        "natural_language": {
            "nlp",
            "text",
            "language",
            "processing",
            "sentiment",
            "parsing",
            "tokenization",
            "embedding",
            "transformer",
            "bert",
            "gpt",
            "translation",
            "summarization",
            "classification",
            "entity",
        },
        "mathematics": {
            "theorem",
            "proof",
            "equation",
            "formula",
            "algebra",
            "calculus",
            "geometry",
            "topology",
            "analysis",
            "statistics",
            "probability",
            "matrix",
            "vector",
            "optimization",
            "numerical",
        },
        "physics": {
            "quantum",
            "relativity",
            "particle",
            "wave",
            "energy",
            "force",
            "field",
            "electromagnetic",
            "thermodynamics",
            "mechanics",
            "photon",
            "electron",
            "nuclear",
            "cosmology",
            "gravity",
        },
        "biology": {
            "gene",
            "protein",
            "dna",
            "rna",
            "cell",
            "molecular",
            "evolution",
            "genome",
            "sequence",
            "mutation",
            "expression",
            "pathway",
            "organism",
            "tissue",
            "metabolism",
            "enzyme",
        },
        "chemistry": {
            "molecule",
            "atom",
            "bond",
            "reaction",
            "catalyst",
            "synthesis",
            "organic",
            "inorganic",
            "polymer",
            "crystal",
            "spectroscopy",
            "compound",
            "element",
            "ionic",
            "covalent",
        },
    }

    # Tag categories
    TAG_CATEGORIES = {
        "methodology": ["method", "approach", "technique", "algorithm", "framework"],
        "application": ["application", "use case", "implementation", "deployment"],
        "theory": ["theory", "theoretical", "mathematical", "formal"],
        "experimental": ["experiment", "empirical", "validation", "evaluation"],
        "dataset": ["dataset", "data", "corpus", "benchmark", "collection"],
        "performance": ["performance", "accuracy", "efficiency", "speed", "metric"],
        "comparison": ["comparison", "versus", "comparative", "baseline"],
        "review": ["survey", "review", "overview", "state-of-art", "literature"],
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the smart tagger."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "tag_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "tags.db"
        self._init_database()

        # Initialize NLTK components if available
        if NLTK_AVAILABLE:
            self._ensure_nltk_data()
            self.stemmer = PorterStemmer()
            self.stop_words = set(stopwords.words("english"))
        else:
            self.stemmer = None
            self.stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "this",
                "that",
                "these",
                "those",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "must",
                "can",
                "cannot",
            }

        logger.info(f"SmartTagger initialized with NLTK: {NLTK_AVAILABLE}")

    def _init_database(self) -> None:
        """Initialize SQLite database for tag persistence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    contexts TEXT,
                    related_terms TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(term, category)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tag_id) REFERENCES tags (id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tags_term ON tags(term)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_paper_tags_paper ON paper_tags(paper_id)
            """
            )

    def _ensure_nltk_data(self) -> None:
        """Ensure required NLTK data is downloaded."""
        required_data = [
            "punkt",
            "stopwords",
            "averaged_perceptron_tagger",
            "maxent_ne_chunker",
            "words",
        ]

        for data_name in required_data:
            try:
                nltk.data.find(f"tokenizers/{data_name}")
            except LookupError:
                try:
                    nltk.download(data_name, quiet=True)
                except Exception as e:
                    logger.warning(f"Could not download NLTK data {data_name}: {e}")

    def extract_tags(self, text: str, title: str = "", abstract: str = "") -> List[Tag]:
        """
        Extract smart tags from text content.

        Args:
            text: Main text content
            title: Paper title (optional)
            abstract: Paper abstract (optional)

        Returns:
            List of extracted tags
        """
        start_time = datetime.now()

        # Combine all text sources
        full_text = f"{title} {abstract} {text}".strip()

        if NLTK_AVAILABLE:
            tags = self._extract_tags_nltk(full_text, title, abstract)
        else:
            tags = self._extract_tags_basic(full_text, title, abstract)

        # Add domain-specific tags
        domain_tags = self._extract_domain_tags(full_text)
        tags.extend(domain_tags)

        # Categorize and deduplicate
        tags = self._categorize_tags(tags)
        tags = self._deduplicate_tags(tags)

        # Score confidence
        for tag in tags:
            tag.confidence = self._calculate_confidence(tag, full_text)

        # Sort by confidence
        tags.sort(key=lambda x: x.confidence, reverse=True)

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Extracted {len(tags)} tags in {processing_time:.2f}s")

        return tags

    def _extract_tags_nltk(self, text: str, title: str, abstract: str) -> List[Tag]:
        """Extract tags using NLTK capabilities."""
        tags = []

        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalnum() and len(token) > 2]
        tokens = [token for token in tokens if token not in self.stop_words]

        # POS tagging to identify nouns and adjectives
        pos_tags = pos_tag(tokens)
        relevant_pos = ["NN", "NNS", "NNP", "NNPS", "JJ", "JJS", "JJR"]

        # Extract meaningful terms
        term_counts = Counter()
        for token, pos in pos_tags:
            if pos in relevant_pos:
                stem = self.stemmer.stem(token) if self.stemmer else token
                term_counts[stem] += 1

        # Named entity recognition
        sentences = sent_tokenize(text)
        for sentence in sentences[:10]:  # Limit for performance
            tokens = word_tokenize(sentence)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)

            for chunk in chunks:
                if hasattr(chunk, "label"):
                    entity = " ".join([token for token, pos in chunk.leaves()])
                    if len(entity) > 2:
                        term_counts[entity.lower()] += 1

        # Convert to Tag objects
        for term, freq in term_counts.most_common(50):
            if freq >= 2 or term in title.lower() or term in abstract.lower():
                tag = Tag(
                    term=term,
                    category="extracted",
                    confidence=0.5,
                    frequency=freq,
                    contexts=[],
                    related_terms=[],
                )
                tags.append(tag)

        return tags

    def _extract_tags_basic(self, text: str, title: str, abstract: str) -> List[Tag]:
        """Extract tags using basic text processing."""
        tags = []

        # Simple word extraction
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        words = [word for word in words if word not in self.stop_words]

        # Count frequencies
        word_counts = Counter(words)

        # Convert to Tag objects
        for word, freq in word_counts.most_common(30):
            if freq >= 2 or word in title.lower() or word in abstract.lower():
                tag = Tag(
                    term=word,
                    category="extracted",
                    confidence=0.5,
                    frequency=freq,
                    contexts=[],
                    related_terms=[],
                )
                tags.append(tag)

        return tags

    def _extract_domain_tags(self, text: str) -> List[Tag]:
        """Extract domain-specific tags."""
        tags = []
        text_lower = text.lower()

        for domain, keywords in self.FIELD_KEYWORDS.items():
            domain_score = 0
            found_keywords = []

            for keyword in keywords:
                if keyword in text_lower:
                    count = text_lower.count(keyword)
                    domain_score += count
                    found_keywords.extend([keyword] * count)

            if domain_score > 0:
                # Add domain tag
                domain_tag = Tag(
                    term=domain.replace("_", " "),
                    category="domain",
                    confidence=min(domain_score / 10.0, 1.0),
                    frequency=domain_score,
                    contexts=[],
                    related_terms=found_keywords,
                )
                tags.append(domain_tag)

                # Add individual keyword tags
                keyword_counts = Counter(found_keywords)
                for keyword, count in keyword_counts.items():
                    if count >= 2:
                        keyword_tag = Tag(
                            term=keyword,
                            category=f"{domain}_keyword",
                            confidence=min(count / 5.0, 1.0),
                            frequency=count,
                            contexts=[],
                            related_terms=[domain.replace("_", " ")],
                        )
                        tags.append(keyword_tag)

        return tags

    def _categorize_tags(self, tags: List[Tag]) -> List[Tag]:
        """Categorize tags based on content analysis."""
        categorized = []

        for tag in tags:
            # Check against category keywords
            best_category = "general"
            best_score = 0

            for category, keywords in self.TAG_CATEGORIES.items():
                score = sum(1 for kw in keywords if kw in tag.term.lower())
                if score > best_score:
                    best_score = score
                    best_category = category

            # Update category if better match found
            if best_score > 0 and tag.category == "extracted":
                tag.category = best_category

            categorized.append(tag)

        return categorized

    def _deduplicate_tags(self, tags: List[Tag]) -> List[Tag]:
        """Remove duplicate tags and merge similar ones."""
        seen_terms = {}
        deduplicated = []

        for tag in tags:
            # Normalize term
            normalized = tag.term.lower().strip()

            if normalized in seen_terms:
                # Merge with existing tag
                existing = seen_terms[normalized]
                existing.frequency += tag.frequency
                existing.confidence = max(existing.confidence, tag.confidence)
                existing.related_terms.extend(tag.related_terms)
                existing.contexts.extend(tag.contexts)
            else:
                seen_terms[normalized] = tag
                deduplicated.append(tag)

        return deduplicated

    def _calculate_confidence(self, tag: Tag, full_text: str) -> float:
        """Calculate confidence score for a tag."""
        base_confidence = tag.confidence

        # Frequency boost
        freq_boost = min(tag.frequency / 10.0, 0.3)

        # Length boost (longer terms are often more specific)
        length_boost = min(len(tag.term.split()) / 5.0, 0.2)

        # Domain relevance boost
        domain_boost = 0.1 if tag.category.endswith("_keyword") else 0

        # Context boost (if term appears in title/abstract context)
        context_boost = (
            0.2 if any("title" in ctx or "abstract" in ctx for ctx in tag.contexts) else 0
        )

        final_confidence = min(
            base_confidence + freq_boost + length_boost + domain_boost + context_boost,
            1.0,
        )
        return round(final_confidence, 3)

    def tag_paper(self, paper_id: str, content: Dict[str, str]) -> TaggingResult:
        """
        Tag a complete paper.

        Args:
            paper_id: Unique paper identifier
            content: Dictionary with 'title', 'abstract', 'text' keys

        Returns:
            TaggingResult with extracted tags and metadata
        """
        start_time = datetime.now()

        title = content.get("title", "")
        abstract = content.get("abstract", "")
        text = content.get("text", "")

        # Extract tags
        tags = self.extract_tags(text, title, abstract)

        # Categorize tags
        categories = defaultdict(list)
        for tag in tags:
            categories[tag.category].append(tag)

        # Calculate overall confidence
        if tags:
            confidence_score = sum(tag.confidence for tag in tags) / len(tags)
        else:
            confidence_score = 0.0

        processing_time = (datetime.now() - start_time).total_seconds()
        method_used = "NLTK-enhanced" if NLTK_AVAILABLE else "basic"

        # Store in database
        self._store_paper_tags(paper_id, tags)

        result = TaggingResult(
            paper_id=paper_id,
            tags=tags,
            categories=dict(categories),
            confidence_score=confidence_score,
            processing_time=processing_time,
            method_used=method_used,
            metadata={
                "total_tags": len(tags),
                "categories_found": len(categories),
                "top_category": (
                    max(categories.keys(), key=lambda k: len(categories[k])) if categories else None
                ),
                "text_length": len(text),
                "has_title": bool(title),
                "has_abstract": bool(abstract),
            },
        )

        logger.info(f"Tagged paper {paper_id}: {len(tags)} tags, {confidence_score:.2f} confidence")
        return result

    def _store_paper_tags(self, paper_id: str, tags: List[Tag]) -> None:
        """Store paper tags in database."""
        with sqlite3.connect(self.db_path) as conn:
            for tag in tags:
                # Insert or update tag
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tags
                    (term, category, confidence, frequency, contexts, related_terms, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        tag.term,
                        tag.category,
                        tag.confidence,
                        tag.frequency,
                        json.dumps(tag.contexts),
                        json.dumps(tag.related_terms),
                        datetime.now(),
                    ),
                )

                # Get tag ID
                tag_id = conn.execute(
                    "SELECT id FROM tags WHERE term = ? AND category = ?",
                    (tag.term, tag.category),
                ).fetchone()[0]

                # Link to paper
                conn.execute(
                    """
                    INSERT OR REPLACE INTO paper_tags
                    (paper_id, tag_id, confidence, context)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        paper_id,
                        tag_id,
                        tag.confidence,
                        f"Auto-tagged with {tag.frequency} occurrences",
                    ),
                )

    def get_paper_tags(self, paper_id: str) -> List[Tag]:
        """Retrieve tags for a specific paper."""
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT t.term, t.category, pt.confidence, t.frequency,
                       t.contexts, t.related_terms, t.first_seen, t.last_used
                FROM tags t
                JOIN paper_tags pt ON t.id = pt.tag_id
                WHERE pt.paper_id = ?
                ORDER BY pt.confidence DESC
            """,
                (paper_id,),
            ).fetchall()

            tags = []
            for row in results:
                tag = Tag(
                    term=row[0],
                    category=row[1],
                    confidence=row[2],
                    frequency=row[3],
                    contexts=json.loads(row[4]) if row[4] else [],
                    related_terms=json.loads(row[5]) if row[5] else [],
                    first_seen=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    last_used=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                )
                tags.append(tag)

            return tags

    def get_trending_tags(self, limit: int = 20, days: int = 30) -> List[Tuple[str, int, float]]:
        """Get trending tags based on recent usage."""
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT t.term, COUNT(pt.id) as usage_count, AVG(pt.confidence) as avg_confidence
                FROM tags t
                JOIN paper_tags pt ON t.id = pt.tag_id
                WHERE pt.created_at >= datetime('now', '-{} days')
                GROUP BY t.term
                ORDER BY usage_count DESC, avg_confidence DESC
                LIMIT ?
            """.format(
                    days
                ),
                (limit,),
            ).fetchall()

            return [(row[0], row[1], row[2]) for row in results]

    def suggest_related_tags(self, tag_term: str, limit: int = 10) -> List[str]:
        """Suggest related tags based on co-occurrence."""
        with sqlite3.connect(self.db_path) as conn:
            # Find papers that contain the given tag
            paper_ids = conn.execute(
                """
                SELECT DISTINCT pt.paper_id
                FROM paper_tags pt
                JOIN tags t ON pt.tag_id = t.id
                WHERE t.term = ?
            """,
                (tag_term,),
            ).fetchall()

            if not paper_ids:
                return []

            paper_id_list = [row[0] for row in paper_ids]
            placeholders = ",".join("?" * len(paper_id_list))

            # Find other tags in those papers
            results = conn.execute(
                f"""
                SELECT t.term, COUNT(*) as co_occurrence
                FROM tags t
                JOIN paper_tags pt ON t.id = pt.tag_id
                WHERE pt.paper_id IN ({placeholders})
                AND t.term != ?
                GROUP BY t.term
                ORDER BY co_occurrence DESC
                LIMIT ?
            """,
                paper_id_list + [tag_term, limit],
            ).fetchall()

            return [row[0] for row in results]

    def export_tags(self, output_path: str, format: str = "json") -> bool:
        """Export tags to file."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get all tags with statistics
                results = conn.execute(
                    """
                    SELECT t.term, t.category, t.confidence, t.frequency,
                           COUNT(pt.id) as paper_count,
                           t.contexts, t.related_terms, t.first_seen, t.last_used
                    FROM tags t
                    LEFT JOIN paper_tags pt ON t.id = pt.tag_id
                    GROUP BY t.id
                    ORDER BY paper_count DESC, t.confidence DESC
                """
                ).fetchall()

                tags_data = []
                for row in results:
                    tag_data = {
                        "term": row[0],
                        "category": row[1],
                        "confidence": row[2],
                        "frequency": row[3],
                        "paper_count": row[4],
                        "contexts": json.loads(row[5]) if row[5] else [],
                        "related_terms": json.loads(row[6]) if row[6] else [],
                        "first_seen": row[7],
                        "last_used": row[8],
                    }
                    tags_data.append(tag_data)

                # Export based on format
                output_file = Path(output_path)

                if format == "json":
                    with open(output_file, "w") as f:
                        json.dump(tags_data, f, indent=2, default=str)
                elif format == "csv":
                    import csv

                    with open(output_file, "w", newline="") as f:
                        if tags_data:
                            writer = csv.DictWriter(f, fieldnames=tags_data[0].keys())
                            writer.writeheader()
                            writer.writerows(tags_data)
                else:
                    raise ValueError(f"Unsupported format: {format}")

                logger.info(f"Exported {len(tags_data)} tags to {output_file}")
                return True

        except Exception as e:
            logger.error(f"Failed to export tags: {e}")
            return False


# Convenience functions
def create_smart_tagger(cache_dir: Optional[str] = None) -> SmartTagger:
    """Create a configured SmartTagger instance."""
    return SmartTagger(cache_dir=cache_dir)


def quick_tag_extraction(text: str, max_tags: int = 10) -> List[str]:
    """Quick tag extraction for simple use cases."""
    tagger = SmartTagger()
    tags = tagger.extract_tags(text)
    return [tag.term for tag in tags[:max_tags]]
