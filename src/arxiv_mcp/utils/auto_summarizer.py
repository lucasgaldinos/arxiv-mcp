"""
Auto-summarization for generating paper summaries using existing text processing.
Provides extractive and abstractive summary generation for academic papers.
"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass

from .optional_deps import safe_import_nltk
from .logging import structured_logger


@dataclass
class SummaryResult:
    """Results from paper summarization."""

    title: str
    abstract: Optional[str]
    extractive_summary: List[str]
    key_points: List[str]
    keywords: List[str]
    summary_length: int
    confidence_score: float
    method_used: str


class AutoSummarizer:
    """Automatic summarization engine for academic papers."""

    def __init__(self):
        """Initialize the auto-summarizer with optional NLP capabilities."""
        self.logger = structured_logger(__name__)

        # Try to import NLTK for enhanced processing
        self.nltk = safe_import_nltk()
        self.nltk_available = self.nltk is not None

        if self.nltk_available:
            try:
                from nltk.corpus import stopwords
                from nltk.tokenize import sent_tokenize, word_tokenize

                self.stopwords = set(stopwords.words("english"))
                self.sent_tokenize = sent_tokenize
                self.word_tokenize = word_tokenize
                self.logger.info("NLTK available for enhanced summarization")
            except Exception as e:
                self.logger.warning(f"NLTK data not available: {e}")
                self.nltk_available = False

        # Fallback to basic processing
        if not self.nltk_available:
            self.stopwords = self._get_basic_stopwords()
            self.sent_tokenize = self._basic_sent_tokenize
            self.word_tokenize = self._basic_word_tokenize
            self.logger.info("Using basic text processing for summarization")

        # Academic keywords for relevance scoring
        self.academic_keywords = {
            "method",
            "approach",
            "algorithm",
            "model",
            "system",
            "framework",
            "analysis",
            "evaluation",
            "experiment",
            "results",
            "findings",
            "conclusion",
            "propose",
            "present",
            "develop",
            "investigate",
            "demonstrate",
            "show",
            "prove",
            "significant",
            "novel",
            "improvement",
        }

    def _get_basic_stopwords(self) -> set:
        """Get basic English stopwords for text processing."""
        return {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "will",
            "with",
            "the",
            "this",
            "but",
            "they",
            "have",
            "had",
            "what",
            "said",
            "each",
            "which",
            "she",
            "do",
            "how",
            "their",
            "if",
            "up",
            "out",
            "many",
            "then",
            "them",
            "these",
            "so",
            "some",
            "her",
            "would",
            "make",
            "like",
            "into",
            "him",
            "time",
            "two",
            "more",
            "go",
            "no",
            "way",
            "could",
            "my",
            "than",
            "first",
            "been",
            "call",
            "who",
            "its",
            "now",
            "find",
            "long",
            "down",
            "day",
            "did",
            "get",
            "come",
            "made",
            "may",
            "part",
        }

    def _basic_sent_tokenize(self, text: str) -> List[str]:
        """Basic sentence tokenization using regex."""
        # Split on periods, exclamation marks, and question marks
        sentences = re.split(r"[.!?]+", text)
        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences

    def _basic_word_tokenize(self, text: str) -> List[str]:
        """Basic word tokenization using regex."""
        # Split on whitespace and punctuation, keep alphanumeric
        words = re.findall(r"\b\w+\b", text.lower())
        return words

    def _calculate_sentence_score(
        self, sentence: str, word_freq: Dict[str, float]
    ) -> float:
        """Calculate relevance score for a sentence."""
        words = self.word_tokenize(sentence)
        words = [w for w in words if w not in self.stopwords and len(w) > 2]

        if not words:
            return 0.0

        # Base score from word frequencies
        score = sum(word_freq.get(word, 0) for word in words) / len(words)

        # Boost for academic keywords
        academic_boost = sum(1 for word in words if word in self.academic_keywords)
        score += academic_boost * 0.1

        # Boost for sentences with numbers (often indicate results)
        if re.search(r"\d+", sentence):
            score += 0.1

        # Penalize very short or very long sentences
        sentence_length = len(words)
        if sentence_length < 5:
            score *= 0.5
        elif sentence_length > 40:
            score *= 0.7

        return score

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms from the text."""
        words = self.word_tokenize(text)
        words = [w for w in words if w not in self.stopwords and len(w) > 3]

        # Count word frequencies
        word_counts = Counter(words)

        # Score words by frequency and academic relevance
        word_scores = {}
        for word, count in word_counts.items():
            score = count
            if word in self.academic_keywords:
                score *= 2
            # Boost technical terms (words with numbers or mixed case patterns)
            if re.search(r"\d+|[A-Z]", word):
                score *= 1.5
            word_scores[word] = score

        # Return top keywords
        sorted_keywords = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_keywords[:max_keywords]]

    def _extract_key_points(
        self, sentences: List[str], max_points: int = 5
    ) -> List[str]:
        """Extract key points from sentences using pattern matching."""
        key_points = []

        # Patterns that often indicate key points in academic papers
        patterns = [
            r"we (propose|present|develop|introduce|demonstrate)",
            r"our (method|approach|algorithm|system|framework)",
            r"(results|findings) (show|indicate|demonstrate|reveal)",
            r"(significant|substantial|notable) (improvement|increase|decrease)",
            r"(conclude|conclusion) that",
            r"(main|key|primary) (contribution|finding|result)",
            r"(novel|new|innovative) (approach|method|algorithm)",
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    key_points.append(sentence)
                    break

            if len(key_points) >= max_points:
                break

        return key_points

    def summarize_paper(
        self,
        title: str,
        abstract: Optional[str] = None,
        content: Optional[str] = None,
        max_sentences: int = 5,
        include_keywords: bool = True,
    ) -> SummaryResult:
        """
        Generate a comprehensive summary of an academic paper.

        Args:
            title: Paper title
            abstract: Paper abstract (if available)
            content: Full paper content (optional)
            max_sentences: Maximum sentences in extractive summary
            include_keywords: Whether to extract keywords

        Returns:
            SummaryResult with summary components
        """
        try:
            # Combine available text
            full_text = ""
            if abstract:
                full_text += f"Abstract: {abstract}\n\n"
            if content:
                full_text += content

            if not full_text.strip():
                return SummaryResult(
                    title=title,
                    abstract=abstract,
                    extractive_summary=[],
                    key_points=[],
                    keywords=[],
                    summary_length=0,
                    confidence_score=0.0,
                    method_used="insufficient_content",
                )

            # Tokenize into sentences
            sentences = self.sent_tokenize(full_text)

            if len(sentences) < 2:
                # Not enough content for summarization
                return SummaryResult(
                    title=title,
                    abstract=abstract,
                    extractive_summary=sentences,
                    key_points=[],
                    keywords=self._extract_keywords(full_text)
                    if include_keywords
                    else [],
                    summary_length=len(sentences),
                    confidence_score=0.3,
                    method_used="minimal_content",
                )

            # Calculate word frequencies
            all_words = self.word_tokenize(full_text)
            filtered_words = [
                w for w in all_words if w not in self.stopwords and len(w) > 2
            ]
            word_freq = Counter(filtered_words)

            # Normalize frequencies
            max_freq = max(word_freq.values()) if word_freq else 1
            word_freq = {word: freq / max_freq for word, freq in word_freq.items()}

            # Score all sentences
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                score = self._calculate_sentence_score(sentence, word_freq)
                sentence_scores.append((score, i, sentence))

            # Select top sentences for summary
            sentence_scores.sort(reverse=True)
            top_sentences = sentence_scores[:max_sentences]

            # Sort by original order to maintain flow
            top_sentences.sort(key=lambda x: x[1])
            extractive_summary = [sentence for _, _, sentence in top_sentences]

            # Extract key points and keywords
            key_points = self._extract_key_points(sentences)
            keywords = self._extract_keywords(full_text) if include_keywords else []

            # Calculate confidence score
            confidence = self._calculate_confidence(
                len(sentences), len(extractive_summary), word_freq, abstract is not None
            )

            method_used = "nltk_enhanced" if self.nltk_available else "basic_processing"
            if abstract and not content:
                method_used += "_abstract_only"

            return SummaryResult(
                title=title,
                abstract=abstract,
                extractive_summary=extractive_summary,
                key_points=key_points,
                keywords=keywords,
                summary_length=len(extractive_summary),
                confidence_score=confidence,
                method_used=method_used,
            )

        except Exception as e:
            self.logger.error(f"Failed to summarize paper '{title}': {e}")
            return SummaryResult(
                title=title,
                abstract=abstract,
                extractive_summary=[],
                key_points=[],
                keywords=[],
                summary_length=0,
                confidence_score=0.0,
                method_used="error",
            )

    def _calculate_confidence(
        self,
        total_sentences: int,
        summary_sentences: int,
        word_freq: Dict[str, float],
        has_abstract: bool,
    ) -> float:
        """Calculate confidence score for the summary."""
        confidence = 0.5  # Base confidence

        # Boost for having sufficient content
        if total_sentences >= 10:
            confidence += 0.2
        elif total_sentences >= 5:
            confidence += 0.1

        # Boost for good compression ratio
        compression_ratio = (
            summary_sentences / total_sentences if total_sentences > 0 else 0
        )
        if 0.1 <= compression_ratio <= 0.3:
            confidence += 0.2

        # Boost for rich vocabulary
        if len(word_freq) > 50:
            confidence += 0.1

        # Boost for having abstract
        if has_abstract:
            confidence += 0.1

        # Boost for NLTK availability
        if self.nltk_available:
            confidence += 0.1

        return min(confidence, 1.0)

    def summarize_multiple_papers(
        self, papers: List[Dict[str, Any]], max_sentences_per_paper: int = 3
    ) -> List[SummaryResult]:
        """Summarize multiple papers efficiently."""
        results = []

        for paper in papers:
            title = paper.get("title", "Untitled")
            abstract = paper.get("abstract")
            content = paper.get("content")

            summary = self.summarize_paper(
                title=title,
                abstract=abstract,
                content=content,
                max_sentences=max_sentences_per_paper,
            )
            results.append(summary)

        return results

    def generate_comparative_summary(
        self, papers: List[Dict[str, Any]], focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comparative summary across multiple papers."""
        if not papers:
            return {}

        # Summarize individual papers
        individual_summaries = self.summarize_multiple_papers(papers)

        # Extract common themes
        all_keywords = []
        all_key_points = []

        for summary in individual_summaries:
            all_keywords.extend(summary.keywords)
            all_key_points.extend(summary.key_points)

        # Find common keywords
        keyword_counts = Counter(all_keywords)
        common_keywords = [word for word, count in keyword_counts.most_common(10)]

        # Calculate average confidence
        avg_confidence = sum(s.confidence_score for s in individual_summaries) / len(
            individual_summaries
        )

        return {
            "paper_count": len(papers),
            "individual_summaries": [
                {
                    "title": summary.title,
                    "summary": summary.extractive_summary,
                    "key_points": summary.key_points,
                    "keywords": summary.keywords,
                }
                for summary in individual_summaries
            ],
            "common_themes": common_keywords,
            "comparative_insights": self._generate_comparative_insights(
                individual_summaries
            ),
            "average_confidence": avg_confidence,
            "focus_topic": focus_topic,
        }

    def _generate_comparative_insights(
        self, summaries: List[SummaryResult]
    ) -> List[str]:
        """Generate insights by comparing multiple paper summaries."""
        insights = []

        # Count methodological approaches
        method_keywords = ["method", "approach", "algorithm", "technique", "framework"]
        method_mentions = defaultdict(int)

        for summary in summaries:
            for keyword in summary.keywords:
                if any(method in keyword.lower() for method in method_keywords):
                    method_mentions[keyword] += 1

        if method_mentions:
            top_method = max(method_mentions, key=method_mentions.get)
            insights.append(f"Most common methodological approach: {top_method}")

        # Analyze result patterns
        result_keywords = ["improvement", "accuracy", "performance", "effectiveness"]
        result_counts = sum(
            sum(
                1
                for keyword in summary.keywords
                if any(res in keyword.lower() for res in result_keywords)
            )
            for summary in summaries
        )

        if result_counts > len(summaries) * 0.5:
            insights.append("Majority of papers report performance improvements")

        # Novel contributions
        novel_keywords = ["novel", "new", "innovative", "first", "original"]
        novel_papers = sum(
            1
            for summary in summaries
            if any(
                any(novel in kw.lower() for novel in novel_keywords)
                for kw in summary.keywords
            )
        )

        if novel_papers > 0:
            insights.append(f"{novel_papers} papers claim novel contributions")

        return insights


# Global summarizer instance
_summarizer_instance = None


def get_auto_summarizer() -> AutoSummarizer:
    """Get the global auto-summarizer instance."""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = AutoSummarizer()
    return _summarizer_instance
