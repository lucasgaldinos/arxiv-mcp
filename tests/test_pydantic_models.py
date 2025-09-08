"""
Test suite for Pydantic models in ArXiv MCP server.
Comprehensive validation testing for all data models.
"""

import pytest
from pydantic import ValidationError

from arxiv_mcp.models import (
    ArxivID,
    Author,
    Citation,
    Paper,
    SearchQuery,
    SummaryResult,
    Tag,
    ReadingList,
    NotificationRule,
    TrendingPaper,
    BatchOperation,
    ArxivIDFormat,
    PaperStatus,
    NotificationRuleType,
    SummaryType,
)


class TestArxivID:
    """Test ArXiv ID validation and format detection."""

    def test_valid_new_format_ids(self):
        """Test valid new format ArXiv IDs."""
        valid_ids = [
            "2301.00001",
            "2301.00001v1",
            "2301.12345v2",
            "1234.5678",
        ]

        for id_str in valid_ids:
            arxiv_id = ArxivID(id=id_str, format=ArxivIDFormat.NEW)
            assert arxiv_id.id == id_str
            assert arxiv_id.format == ArxivIDFormat.NEW

    def test_valid_old_format_ids(self):
        """Test valid old format ArXiv IDs."""
        valid_ids = [
            "math.GT/0601001",
            "cs.LG/0601001v1",
            "physics.gen-ph/0601001",
            "astro-ph/0601001v2",
        ]

        for id_str in valid_ids:
            arxiv_id = ArxivID(id=id_str, format=ArxivIDFormat.OLD)
            assert arxiv_id.id == id_str
            assert arxiv_id.format == ArxivIDFormat.OLD

    def test_invalid_arxiv_ids(self):
        """Test invalid ArXiv ID formats."""
        invalid_ids = [
            "invalid",
            "123",
            "2301",
            "2301.",
            "2301.abc",
            "",
            "math/123",  # Too few digits
        ]

        for id_str in invalid_ids:
            with pytest.raises(ValidationError):
                ArxivID(id=id_str, format=ArxivIDFormat.NEW)


class TestAuthor:
    """Test Author model validation."""

    def test_valid_author(self):
        """Test valid author creation."""
        author = Author(
            name="John Doe",
            affiliation="MIT",
            email="john.doe@mit.edu",
            orcid="0000-0000-0000-0000",
        )

        assert author.name == "John Doe"
        assert author.affiliation == "MIT"
        assert author.email == "john.doe@mit.edu"
        assert author.orcid == "0000-0000-0000-0000"

    def test_invalid_email(self):
        """Test invalid email validation."""
        with pytest.raises(ValidationError):
            Author(name="John Doe", email="invalid-email")

    def test_empty_name(self):
        """Test empty name validation."""
        with pytest.raises(ValidationError):
            Author(name="")


class TestCitation:
    """Test Citation model validation."""

    def test_valid_citation(self):
        """Test valid citation creation."""
        citation = Citation(
            authors=["John Doe", "Jane Smith"],
            title="Test Paper",
            year="2023",
            journal="Test Journal",
            confidence=0.95,
            raw_text="John Doe, Jane Smith. Test Paper. Test Journal, 2023.",
        )

        assert len(citation.authors) == 2
        assert citation.title == "Test Paper"
        assert citation.confidence == 0.95

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        citation = Citation(confidence=0.5)
        assert citation.confidence == 0.5

        # Invalid confidence values
        with pytest.raises(ValidationError):
            Citation(confidence=-0.1)

        with pytest.raises(ValidationError):
            Citation(confidence=1.1)


class TestPaper:
    """Test Paper model validation."""

    def test_valid_paper(self):
        """Test valid paper creation."""
        paper = Paper(
            arxiv_id="2301.00001",
            title="Test Paper",
            authors=[Author(name="John Doe"), Author(name="Jane Smith")],
            abstract="This is a test abstract.",
            categories=["cs.LG", "cs.AI"],
            status=PaperStatus.COMPLETED,
        )

        assert paper.arxiv_id == "2301.00001"
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2
        assert paper.status == PaperStatus.COMPLETED

    def test_invalid_arxiv_id(self):
        """Test invalid ArXiv ID in paper."""
        with pytest.raises(ValidationError):
            Paper(arxiv_id="invalid", title="Test Paper")

    def test_empty_title(self):
        """Test empty title validation."""
        with pytest.raises(ValidationError):
            Paper(arxiv_id="2301.00001", title="")


class TestSearchQuery:
    """Test SearchQuery model validation."""

    def test_valid_search_query(self):
        """Test valid search query creation."""
        query = SearchQuery(
            query="machine learning",
            user_id="user123",
            categories=["cs.LG"],
            max_results=100,
        )

        assert query.query == "machine learning"
        assert query.user_id == "user123"
        assert query.max_results == 100

    def test_max_results_validation(self):
        """Test max_results bounds validation."""
        # Valid values
        query = SearchQuery(query="test", max_results=50)
        assert query.max_results == 50

        # Invalid values
        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_results=0)

        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_results=1001)

    def test_empty_query(self):
        """Test empty query validation."""
        with pytest.raises(ValidationError):
            SearchQuery(query="")


class TestSummaryResult:
    """Test SummaryResult model validation."""

    def test_valid_summary_result(self):
        """Test valid summary result creation."""
        result = SummaryResult(
            summary_text="This is a test summary.",
            summary_type=SummaryType.EXTRACTIVE,
            confidence=0.8,
            key_phrases=["machine learning", "neural networks"],
            word_count=100,
            compression_ratio=0.3,
        )

        assert result.summary_text == "This is a test summary."
        assert result.summary_type == SummaryType.EXTRACTIVE
        assert result.confidence == 0.8
        assert len(result.key_phrases) == 2

    def test_compression_ratio_validation(self):
        """Test compression ratio bounds validation."""
        # Valid values
        result = SummaryResult(compression_ratio=0.5)
        assert result.compression_ratio == 0.5

        # Invalid values
        with pytest.raises(ValidationError):
            SummaryResult(compression_ratio=-0.1)

        with pytest.raises(ValidationError):
            SummaryResult(compression_ratio=1.1)


class TestTag:
    """Test Tag model validation."""

    def test_valid_tag(self):
        """Test valid tag creation."""
        tag = Tag(
            text="machine learning", category="algorithm", confidence=0.9, frequency=5
        )

        assert tag.text == "machine learning"
        assert tag.category == "algorithm"
        assert tag.confidence == 0.9
        assert tag.frequency == 5

    def test_empty_text(self):
        """Test empty tag text validation."""
        with pytest.raises(ValidationError):
            Tag(text="")

    def test_frequency_validation(self):
        """Test frequency minimum validation."""
        with pytest.raises(ValidationError):
            Tag(text="test", frequency=0)


class TestReadingList:
    """Test ReadingList model validation."""

    def test_valid_reading_list(self):
        """Test valid reading list creation."""
        reading_list = ReadingList(
            name="AI Papers",
            description="Papers about artificial intelligence",
            user_id="user123",
            papers=[
                Paper(arxiv_id="2301.00001", title="Test Paper 1"),
                Paper(arxiv_id="2301.00002", title="Test Paper 2"),
            ],
            is_public=True,
            tags=["AI", "ML"],
        )

        assert reading_list.name == "AI Papers"
        assert reading_list.user_id == "user123"
        assert len(reading_list.papers) == 2
        assert reading_list.is_public is True

    def test_empty_name(self):
        """Test empty list name validation."""
        with pytest.raises(ValidationError):
            ReadingList(name="", user_id="user123")


class TestNotificationRule:
    """Test NotificationRule model validation."""

    def test_valid_notification_rule(self):
        """Test valid notification rule creation."""
        rule = NotificationRule(
            user_id="user123",
            rule_type=NotificationRuleType.KEYWORD,
            criteria={"keywords": ["machine learning"]},
            enabled=True,
        )

        assert rule.user_id == "user123"
        assert rule.rule_type == NotificationRuleType.KEYWORD
        assert rule.criteria["keywords"] == ["machine learning"]
        assert rule.enabled is True


class TestBatchOperation:
    """Test BatchOperation model validation."""

    def test_valid_batch_operation(self):
        """Test valid batch operation creation."""
        operation = BatchOperation(
            operation_type="download",
            items=["item1", "item2", "item3"],
            concurrency=3,
            timeout=600.0,
            retry_count=2,
        )

        assert operation.operation_type == "download"
        assert len(operation.items) == 3
        assert operation.concurrency == 3
        assert operation.timeout == 600.0

    def test_concurrency_bounds(self):
        """Test concurrency bounds validation."""
        # Valid values
        operation = BatchOperation(
            operation_type="test", items=["item1"], concurrency=10
        )
        assert operation.concurrency == 10

        # Invalid values
        with pytest.raises(ValidationError):
            BatchOperation(operation_type="test", items=["item1"], concurrency=0)

        with pytest.raises(ValidationError):
            BatchOperation(operation_type="test", items=["item1"], concurrency=25)


class TestTrendingPaper:
    """Test TrendingPaper model validation."""

    def test_valid_trending_paper(self):
        """Test valid trending paper creation."""
        trending = TrendingPaper(
            arxiv_id="2301.00001",
            title="Trending Paper",
            trending_score=0.95,
            velocity=0.1,
            peak_position=1,
            social_mentions=100,
        )

        assert trending.arxiv_id == "2301.00001"
        assert trending.trending_score == 0.95
        assert trending.peak_position == 1
        assert trending.social_mentions == 100


class TestModelIntegration:
    """Test model integration and relationships."""

    def test_paper_with_authors_and_citations(self):
        """Test complex paper creation with related models."""
        authors = [
            Author(name="John Doe", email="john@example.com"),
            Author(name="Jane Smith", affiliation="MIT"),
        ]

        paper = Paper(
            arxiv_id="2301.00001",
            title="Complex Test Paper",
            authors=authors,
            abstract="A complex paper for testing.",
            categories=["cs.LG", "cs.AI"],
            status=PaperStatus.COMPLETED,
            downloads=100,
            citations=50,
        )

        assert len(paper.authors) == 2
        assert paper.authors[0].name == "John Doe"
        assert paper.authors[1].affiliation == "MIT"
        assert paper.downloads == 100
        assert paper.citations == 50

    def test_reading_list_with_papers(self):
        """Test reading list containing multiple papers."""
        papers = [
            Paper(arxiv_id="2301.00001", title="Paper 1"),
            Paper(arxiv_id="2301.00002", title="Paper 2"),
            Paper(arxiv_id="2301.00003", title="Paper 3"),
        ]

        reading_list = ReadingList(
            name="Test Collection",
            user_id="user123",
            papers=papers,
            tags=["collection", "test"],
        )

        assert len(reading_list.papers) == 3
        assert all(isinstance(p, Paper) for p in reading_list.papers)
        assert reading_list.tags == ["collection", "test"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
