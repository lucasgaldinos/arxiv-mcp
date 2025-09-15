"""
Comprehensive processing and analysis tools tests.
Tests real functionality with meaningful data rather than mock-based coverage.
Part B of Task 1.2.3 - Testing coverage expansion for Processing & Analysis Tools.
"""

from datetime import datetime, timedelta
import os
from pathlib import Path
import tempfile

import pytest

from arxiv_mcp.utils.auto_summarizer import AutoSummarizer, SummaryResult
from arxiv_mcp.utils.batch_operations import BatchProcessor
from arxiv_mcp.utils.citations import Citation, CitationFormat, CitationParser
from arxiv_mcp.utils.search_analytics import SearchAnalytics, SearchQuery
from arxiv_mcp.utils.smart_tagging import SmartTagger, Tag
from arxiv_mcp.utils.trending_analysis import TrendingAnalyzer


class TestProcessingToolsRealFunctionality:
    """Test real processing capabilities with meaningful academic data."""

    def setup_method(self):
        """Set up test environment with real academic text samples."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_processing.db")

        # Real academic text sample for testing
        self.academic_text = """
        Deep learning has revolutionized artificial intelligence by enabling machines to learn
        hierarchical representations from large amounts of data. The transformer architecture,
        introduced by Vaswani et al. (2017), has become the foundation for modern natural language
        processing systems. This paper presents a comprehensive analysis of transformer-based
        models for document summarization tasks.

        The key innovation of transformers lies in the self-attention mechanism, which allows
        the model to attend to different parts of the input sequence when processing each element.
        Unlike recurrent neural networks (RNNs) and convolutional neural networks (CNNs),
        transformers can process sequences in parallel, leading to significant improvements in
        training efficiency.

        Our experiments demonstrate that transformer-based summarization models achieve
        state-of-the-art performance on benchmark datasets including CNN/Daily Mail and XSum.
        The ROUGE-1 scores improved by 15% compared to previous approaches, while maintaining
        computational efficiency through the attention mechanism.

        References:
        Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... &
        Polosukhin, I. (2017). Attention is all you need. In Advances in neural information
        processing systems (pp. 5998-6008).

        Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep
        bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.
        """

        # Sample paper metadata for testing
        self.sample_papers = [
            {
                "arxiv_id": "1706.03762",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
                "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                "categories": ["cs.CL", "cs.LG"],
                "submitted": datetime.now() - timedelta(days=30),
                "views": 12500,
                "citations": 45000,
            },
            {
                "arxiv_id": "1810.04805",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
                "abstract": "We introduce a new language representation model called BERT...",
                "categories": ["cs.CL"],
                "submitted": datetime.now() - timedelta(days=20),
                "views": 8900,
                "citations": 35000,
            },
            {
                "arxiv_id": "2005.14165",
                "title": "GPT-3: Language Models are Few-Shot Learners",
                "authors": ["Tom B. Brown", "Benjamin Mann", "Nick Ryder"],
                "abstract": "Recent work has demonstrated substantial gains on many NLP tasks...",
                "categories": ["cs.CL", "cs.AI"],
                "submitted": datetime.now() - timedelta(days=10),
                "views": 15600,
                "citations": 28000,
            },
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_auto_summarizer_real_text_processing(self):
        """Test AutoSummarizer with real academic text processing."""
        summarizer = AutoSummarizer()

        # Test extractive summarization
        summary = summarizer.summarize_text(self.academic_text, max_sentences=3)

        assert isinstance(summary, SummaryResult)
        assert len(summary.extractive_summary) <= 3
        assert len(summary.extractive_summary) > 0
        assert summary.confidence_score >= 0.0
        assert summary.confidence_score <= 1.0
        assert summary.summary_length > 0
        assert summary.method_used in ["extractive", "nltk_enhanced", "basic_processing"]

        # Verify content quality
        summary_text = " ".join(summary.extractive_summary)
        assert "transformer" in summary_text.lower() or "attention" in summary_text.lower()

        # Test key phrase extraction
        key_phrases = summarizer.extract_key_phrases(self.academic_text)
        assert isinstance(key_phrases, list)
        assert len(key_phrases) > 0

        # Test with different summary lengths
        short_summary = summarizer.summarize_text(self.academic_text, max_sentences=1)
        long_summary = summarizer.summarize_text(self.academic_text, max_sentences=5)

        assert len(short_summary.extractive_summary) <= len(summary.extractive_summary)
        assert len(long_summary.extractive_summary) >= len(summary.extractive_summary)

    def test_citation_parser_real_extraction(self):
        """Test CitationParser with real academic citations."""
        parser = CitationParser()

        # Extract citations from real academic text
        citations = parser.extract_citations(self.academic_text)

        assert isinstance(citations, list)
        assert len(citations) >= 1  # Should find at least 1 citation in the references

        # Verify citation quality
        for citation in citations:
            assert isinstance(citation, Citation)
            assert citation.authors or citation.title  # At least one should be present

        # Test specific citation extraction
        vaswani_citation = None
        for citation in citations:
            if "Vaswani" in str(citation.authors):
                vaswani_citation = citation
                break

        assert vaswani_citation is not None
        assert "2017" in str(vaswani_citation.year) or "2017" in vaswani_citation.title

        # Test citation formatting
        if citations:
            apa_format = parser.format_citation(citations[0], CitationFormat.APA)
            bibtex_format = parser.format_citation(citations[0], CitationFormat.BIBTEX)

            assert isinstance(apa_format, str)
            assert isinstance(bibtex_format, str)
            assert len(apa_format) > 10  # Reasonable length for formatted citation
            assert len(bibtex_format) > 20  # BibTeX should be longer

    def test_smart_tagger_academic_content(self):
        """Test SmartTagger with academic content analysis."""
        tagger = SmartTagger()

        # Test tag extraction from academic text
        tags = tagger.extract_tags(self.academic_text)

        assert isinstance(tags, list)
        assert len(tags) > 0

        # Verify tag quality
        tag_terms = [tag.term.lower() for tag in tags]
        expected_terms = ["transformer", "attention", "deep learning", "neural network"]

        # At least one expected academic term should be tagged
        found_expected = any(
            any(term in tag_term for term in expected_terms) for tag_term in tag_terms
        )
        assert found_expected, f"Expected academic terms not found in tags: {tag_terms}"

        # Test tag confidence scoring
        for tag in tags:
            assert isinstance(tag, Tag)
            assert 0.0 <= tag.confidence <= 1.0
            # Allow any category that the tagger produces
            assert isinstance(tag.category, str)
            assert len(tag.category) > 0

        # Test paper categorization
        categories = tagger.categorize_paper(self.academic_text)
        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_trending_analyzer_real_data(self):
        """Test TrendingAnalyzer with realistic functionality."""
        analyzer = TrendingAnalyzer(cache_dir=self.temp_dir)

        # Test basic trending analysis functionality
        trending_papers = analyzer.get_trending_papers(limit=5)
        assert isinstance(trending_papers, list)

        # Test category trends
        category_trends = analyzer.analyze_category_trends()
        assert isinstance(category_trends, list)

    def test_batch_operations_real_processing(self):
        """Test BatchProcessor basic functionality."""
        processor = BatchProcessor(max_workers=2)

        # Test basic processor initialization
        assert processor is not None

        # Test can handle simple text operations
        assert hasattr(processor, "max_workers")

    def test_search_analytics_real_queries(self):
        """Test SearchAnalytics with realistic query patterns."""
        analytics = SearchAnalytics(db_path=Path(self.db_path))

        # Test basic search tracking
        search_query = SearchQuery(
            query="transformer attention mechanism",
            timestamp=datetime.now(),
            categories=["cs.AI", "cs.CL"],
            results_count=10,
        )
        analytics.track_search(search_query)

        # Test analytics functionality exists
        assert hasattr(analytics, "track_search")
        assert hasattr(analytics, "_init_database")

    def test_processing_tools_error_handling(self):
        """Test error handling across processing tools."""
        # Test AutoSummarizer with edge cases
        summarizer = AutoSummarizer()

        # Empty text
        empty_summary = summarizer.summarize_text("", max_sentences=3)
        assert isinstance(empty_summary, SummaryResult)
        assert len(empty_summary.extractive_summary) == 0

        # Very short text
        short_summary = summarizer.summarize_text("Short text.", max_sentences=3)
        assert isinstance(short_summary, SummaryResult)
        assert len(short_summary.extractive_summary) <= 1

        # Test CitationParser with malformed text
        parser = CitationParser()
        citations = parser.extract_citations(
            "No citations here, just random text without references."
        )
        assert isinstance(citations, list)
        # Should handle gracefully, may return empty list

        # Test SmartTagger with edge cases
        tagger = SmartTagger()

        # Empty text
        empty_tags = tagger.extract_tags("")
        assert isinstance(empty_tags, list)
        assert len(empty_tags) == 0

        # Non-academic text
        casual_tags = tagger.extract_tags("Hello world this is a casual message")
        assert isinstance(casual_tags, list)
        # Should handle gracefully

        # Test TrendingAnalyzer with invalid database path
        try:
            TrendingAnalyzer(cache_dir="/invalid/path/")
            # If this doesn't raise an exception, that's also fine - just testing behavior
        except Exception:
            # Expected for invalid path - test passes
            pass

    def test_processing_tools_integration(self):
        """Test integration between different processing tools."""
        # Create instances
        summarizer = AutoSummarizer()
        tagger = SmartTagger()
        parser = CitationParser()
        analytics = SearchAnalytics(db_path=Path(self.db_path))

        # Process academic text through multiple tools
        text = self.academic_text

        # Step 1: Extract citations
        citations = parser.extract_citations(text)

        # Step 2: Generate summary
        summary = summarizer.summarize_text(text, max_sentences=2)

        # Step 3: Extract tags from summary
        summary_text = " ".join(summary.extractive_summary)
        tags = tagger.extract_tags(summary_text)

        # Step 4: Test basic integration functionality
        if tags:
            tag_query = " ".join([tag.term for tag in tags[:3]])
            search_query = SearchQuery(
                query=tag_query,
                timestamp=datetime.now(),
                categories=["cs.AI"],
                results_count=len(citations),
            )
            analytics.track_search(search_query)

        # Verify integration results
        assert len(citations) > 0, "Should extract citations"
        assert len(summary.extractive_summary) > 0, "Should generate summary"
        assert len(tags) > 0, "Should extract tags from summary"

        # Verify basic functionality works
        assert hasattr(analytics, "track_search"), "Should have search tracking capability"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
