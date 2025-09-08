"""
Pydantic models for ArXiv MCP server data validation and serialization.
Enhanced type safety and validation for all data structures.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pathlib import Path


class ArxivIDFormat(str, Enum):
    """ArXiv ID format enumeration."""

    NEW = "new"  # YYMM.NNNN format
    OLD = "old"  # subject-class/YYMMnnn format


class PaperStatus(str, Enum):
    """Paper processing status."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationRuleType(str, Enum):
    """Notification rule types."""

    KEYWORD = "keyword"
    AUTHOR = "author"
    CATEGORY = "category"
    UPDATE = "update"


class SummaryType(str, Enum):
    """Summary generation types."""

    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    KEYWORD = "keyword"


class BaseArxivModel(BaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class ArxivID(BaseArxivModel):
    """Validated ArXiv ID with format detection."""

    id: str = Field(..., description="ArXiv paper ID")
    format: ArxivIDFormat = Field(..., description="ID format (new/old)")
    version: Optional[str] = Field(None, description="Version number if specified")

    @field_validator("id")
    @classmethod
    def validate_arxiv_id(cls, v: str) -> str:
        """Validate ArXiv ID format."""
        import re

        # New format: YYMM.NNNN[vN]
        new_pattern = r"^(\d{4}\.\d{4,5})(v\d+)?$"
        # Old format: subject-class/YYMMnnn[vN] (allows dots and hyphens in subject-class)
        old_pattern = r"^([\w.-]+/\d{7})(v\d+)?$"

        if re.match(new_pattern, v):
            return v
        elif re.match(old_pattern, v):
            return v
        else:
            raise ValueError(f"Invalid ArXiv ID format: {v}")

    @field_validator("format")
    @classmethod
    def detect_format(cls, v: ArxivIDFormat, info) -> ArxivIDFormat:
        """Auto-detect format based on ID."""
        if hasattr(info, "data") and "id" in info.data:
            arxiv_id = info.data["id"]
            if "." in arxiv_id and "/" not in arxiv_id:
                return ArxivIDFormat.NEW
            elif "/" in arxiv_id:
                return ArxivIDFormat.OLD
        return v


class Author(BaseArxivModel):
    """Author information with validation."""

    name: str = Field(..., min_length=1, description="Author full name")
    affiliation: Optional[str] = Field(None, description="Author affiliation")
    email: Optional[str] = Field(None, description="Author email")
    orcid: Optional[str] = Field(None, description="Author ORCID ID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v is None:
            return v
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError(f"Invalid email format: {v}")
        return v


class Citation(BaseArxivModel):
    """Enhanced citation model with validation."""

    authors: List[str] = Field(default_factory=list, description="Citation authors")
    title: str = Field("", description="Citation title")
    year: Optional[str] = Field(None, description="Publication year")
    journal: Optional[str] = Field(None, description="Journal name")
    volume: Optional[str] = Field(None, description="Volume number")
    issue: Optional[str] = Field(None, description="Issue number")
    pages: Optional[str] = Field(None, description="Page numbers")
    doi: Optional[str] = Field(None, description="DOI")
    arxiv_id: Optional[str] = Field(None, description="ArXiv ID if applicable")
    url: Optional[str] = Field(None, description="URL")
    raw_text: str = Field("", description="Original citation text")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Parsing confidence")
    citation_type: str = Field("unknown", description="Citation type")


class Paper(BaseArxivModel):
    """Enhanced paper model with comprehensive validation."""

    arxiv_id: str = Field(..., description="ArXiv ID")
    title: str = Field(..., min_length=1, description="Paper title")
    authors: List[Author] = Field(default_factory=list, description="Paper authors")
    abstract: str = Field("", description="Paper abstract")
    categories: List[str] = Field(default_factory=list, description="ArXiv categories")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    updated_date: Optional[datetime] = Field(None, description="Last update date")
    doi: Optional[str] = Field(None, description="DOI")
    journal_ref: Optional[str] = Field(None, description="Journal reference")
    comments: Optional[str] = Field(None, description="Author comments")
    license: Optional[str] = Field(None, description="License information")

    # Processing metadata
    status: PaperStatus = Field(PaperStatus.PENDING, description="Processing status")
    download_url: Optional[str] = Field(None, description="PDF download URL")
    local_path: Optional[Path] = Field(None, description="Local file path")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    checksum: Optional[str] = Field(None, description="File checksum")

    # Analytics
    downloads: int = Field(0, ge=0, description="Download count")
    citations: int = Field(0, ge=0, description="Citation count")
    views: int = Field(0, ge=0, description="View count")

    @field_validator("arxiv_id")
    @classmethod
    def validate_arxiv_id(cls, v: str) -> str:
        """Validate ArXiv ID format."""
        import re

        # New format: YYMM.NNNN[vN]
        new_pattern = r"^(\d{4}\.\d{4,5})(v\d+)?$"
        # Old format: subject-class/YYMMnnn[vN] (allows dots and hyphens in subject-class)
        old_pattern = r"^([\w.-]+/\d{7})(v\d+)?$"

        if re.match(new_pattern, v) or re.match(old_pattern, v):
            return v
        else:
            raise ValueError(f"Invalid ArXiv ID format: {v}")


class SearchQuery(BaseArxivModel):
    """Enhanced search query with validation."""

    query: str = Field(..., min_length=1, description="Search query text")
    user_id: Optional[str] = Field(None, description="User identifier")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    categories: List[str] = Field(default_factory=list, description="ArXiv categories")
    date_range: Optional[Dict[str, datetime]] = Field(
        None, description="Date range filter"
    )
    max_results: int = Field(50, ge=1, le=1000, description="Maximum results")
    sort_by: str = Field("relevance", description="Sort criteria")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Query timestamp"
    )


class SummaryResult(BaseArxivModel):
    """Text summarization result with metadata."""

    summary_text: str = Field("", description="Generated summary")
    summary_type: SummaryType = Field(
        SummaryType.EXTRACTIVE, description="Summary type"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Summary confidence")
    key_phrases: List[str] = Field(
        default_factory=list, description="Extracted key phrases"
    )
    word_count: int = Field(0, ge=0, description="Summary word count")
    compression_ratio: float = Field(
        0.0, ge=0.0, le=1.0, description="Compression ratio"
    )
    processing_time: float = Field(
        0.0, ge=0.0, description="Processing time in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class Tag(BaseArxivModel):
    """Smart tag with confidence and category."""

    text: str = Field(..., min_length=1, description="Tag text")
    category: str = Field("general", description="Tag category")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Tag confidence")
    frequency: int = Field(1, ge=1, description="Tag frequency in text")
    source: str = Field("auto", description="Tag source (auto/manual)")


class ReadingList(BaseArxivModel):
    """Reading list with papers and metadata."""

    id: Optional[str] = Field(None, description="List ID")
    name: str = Field(..., min_length=1, description="List name")
    description: str = Field("", description="List description")
    user_id: str = Field(..., description="Owner user ID")
    papers: List[Paper] = Field(default_factory=list, description="Papers in list")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    updated_date: datetime = Field(
        default_factory=datetime.now, description="Last update"
    )
    is_public: bool = Field(False, description="Public visibility")
    tags: List[str] = Field(default_factory=list, description="List tags")


class NotificationRule(BaseArxivModel):
    """Notification rule with validation."""

    id: Optional[str] = Field(None, description="Rule ID")
    user_id: str = Field(..., description="User ID")
    rule_type: NotificationRuleType = Field(..., description="Rule type")
    criteria: Dict[str, Any] = Field(..., description="Rule criteria")
    enabled: bool = Field(True, description="Rule enabled status")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    last_triggered: Optional[datetime] = Field(None, description="Last trigger time")
    trigger_count: int = Field(0, ge=0, description="Number of triggers")


class Notification(BaseArxivModel):
    """Notification message with metadata."""

    id: Optional[str] = Field(None, description="Notification ID")
    user_id: str = Field(..., description="Target user ID")
    rule_id: str = Field(..., description="Source rule ID")
    paper_id: str = Field(..., description="Related paper ID")
    message: str = Field(..., min_length=1, description="Notification message")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    read: bool = Field(False, description="Read status")
    priority: str = Field("normal", description="Notification priority")


class TrendingPaper(Paper):
    """Trending paper with additional metrics."""

    trending_score: float = Field(0.0, ge=0.0, description="Trending score")
    velocity: float = Field(0.0, description="Growth velocity")
    peak_position: Optional[int] = Field(
        None, ge=1, description="Peak ranking position"
    )
    trending_categories: List[str] = Field(
        default_factory=list, description="Trending categories"
    )
    social_mentions: int = Field(0, ge=0, description="Social media mentions")


class BatchOperation(BaseArxivModel):
    """Batch operation configuration."""

    id: Optional[str] = Field(None, description="Operation ID")
    operation_type: str = Field(..., description="Type of operation")
    items: List[Any] = Field(..., description="Items to process")
    concurrency: int = Field(5, ge=1, le=20, description="Concurrent workers")
    timeout: float = Field(300.0, gt=0, description="Operation timeout")
    retry_count: int = Field(3, ge=0, description="Retry attempts")
    created_date: datetime = Field(
        default_factory=datetime.now, description="Creation date"
    )
    status: str = Field("pending", description="Operation status")


class BatchResult(BaseArxivModel):
    """Batch operation result."""

    operation_id: str = Field(..., description="Operation ID")
    total_items: int = Field(..., ge=0, description="Total items processed")
    successful_items: int = Field(..., ge=0, description="Successfully processed items")
    failed_items: int = Field(..., ge=0, description="Failed items")
    processing_time: float = Field(..., ge=0, description="Total processing time")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Individual results"
    )
    errors: List[str] = Field(default_factory=list, description="Error messages")
    completed_date: datetime = Field(
        default_factory=datetime.now, description="Completion date"
    )


# Export all models
__all__ = [
    "ArxivID",
    "Author",
    "Citation",
    "Paper",
    "SearchQuery",
    "SummaryResult",
    "Tag",
    "ReadingList",
    "NotificationRule",
    "Notification",
    "TrendingPaper",
    "BatchOperation",
    "BatchResult",
    "ArxivIDFormat",
    "PaperStatus",
    "NotificationRuleType",
    "SummaryType",
]
