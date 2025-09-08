#!/usr/bin/env python3
"""
Reading Lists Management for ArXiv MCP

This module provides personal collection and bookmarking capabilities
for research papers, enabling users to organize and manage their reading.
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timedelta
import uuid

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class Paper:
    """Represents a research paper in a reading list."""

    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str = ""
    categories: List[str] = field(default_factory=list)
    submitted_date: Optional[datetime] = None
    url: str = ""
    pdf_url: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    rating: Optional[int] = None  # 1-5 stars
    read_status: str = "unread"  # unread, reading, read, archived
    added_date: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None


@dataclass
class ReadingList:
    """Represents a collection of papers organized by topic or purpose."""

    id: str
    name: str
    description: str
    papers: List[Paper] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    is_public: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReadingProgress:
    """Tracks reading progress and statistics."""

    paper_id: str
    list_id: str
    progress_percentage: float = 0.0
    time_spent: timedelta = field(default_factory=timedelta)
    bookmarks: List[Dict[str, Any]] = field(default_factory=list)  # page/section bookmarks
    highlights: List[Dict[str, Any]] = field(default_factory=list)  # text highlights
    session_count: int = 0
    last_session: Optional[datetime] = None
    completion_date: Optional[datetime] = None


@dataclass
class ReadingStatistics:
    """Reading statistics and analytics."""

    total_papers: int
    read_papers: int
    reading_papers: int
    unread_papers: int
    total_time_spent: timedelta
    average_time_per_paper: timedelta
    favorite_categories: List[str]
    reading_streak: int
    papers_per_month: Dict[str, int]
    top_authors: List[str]


class ReadingListManager:
    """
    Comprehensive reading list management system.

    Features:
    - Create and manage multiple reading lists
    - Paper bookmarking and organization
    - Reading progress tracking
    - Notes and annotations
    - Search and filtering
    - Import/export functionality
    - Reading statistics and analytics
    """

    READ_STATUSES = ["unread", "reading", "read", "archived"]

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the reading list manager."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "reading_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "reading_lists.db"
        self._init_database()

        logger.info(f"ReadingListManager initialized with cache: {self.cache_dir}")

    def _init_database(self) -> None:
        """Initialize SQLite database for persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            # Reading lists table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reading_lists (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_public BOOLEAN DEFAULT 0,
                    metadata TEXT
                )
            """
            )

            # Papers table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    categories TEXT,
                    submitted_date TIMESTAMP,
                    url TEXT,
                    pdf_url TEXT,
                    tags TEXT,
                    notes TEXT,
                    rating INTEGER,
                    read_status TEXT DEFAULT 'unread',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """
            )

            # List-paper associations
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS list_papers (
                    list_id TEXT,
                    arxiv_id TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    position INTEGER,
                    PRIMARY KEY (list_id, arxiv_id),
                    FOREIGN KEY (list_id) REFERENCES reading_lists (id),
                    FOREIGN KEY (arxiv_id) REFERENCES papers (arxiv_id)
                )
            """
            )

            # Reading progress table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reading_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT,
                    list_id TEXT,
                    progress_percentage REAL DEFAULT 0.0,
                    time_spent INTEGER DEFAULT 0,
                    bookmarks TEXT,
                    highlights TEXT,
                    session_count INTEGER DEFAULT 0,
                    last_session TIMESTAMP,
                    completion_date TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES papers (arxiv_id),
                    FOREIGN KEY (list_id) REFERENCES reading_lists (id)
                )
            """
            )

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(read_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_rating ON papers(rating)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_list_papers_list ON list_papers(list_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_progress_paper ON reading_progress(paper_id)"
            )

    def create_reading_list(
        self, name: str, description: str = "", tags: List[str] = None
    ) -> ReadingList:
        """Create a new reading list."""
        list_id = str(uuid.uuid4())
        tags = tags or []

        reading_list = ReadingList(id=list_id, name=name, description=description, tags=tags)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO reading_lists (id, name, description, tags, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (list_id, name, description, json.dumps(tags), json.dumps({})),
            )

        logger.info(f"Created reading list: {name} ({list_id})")
        return reading_list

    def get_reading_list(self, list_id: str) -> Optional[ReadingList]:
        """Retrieve a reading list by ID."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT id, name, description, tags, created_date, modified_date, is_public, metadata
                FROM reading_lists WHERE id = ?
            """,
                (list_id,),
            ).fetchone()

            if not result:
                return None

            # Get papers in this list
            papers = self._get_papers_in_list(list_id)

            reading_list = ReadingList(
                id=result[0],
                name=result[1],
                description=result[2] or "",
                papers=papers,
                tags=json.loads(result[3]) if result[3] else [],
                created_date=datetime.fromisoformat(result[4]) if result[4] else datetime.now(),
                modified_date=datetime.fromisoformat(result[5]) if result[5] else datetime.now(),
                is_public=bool(result[6]),
                metadata=json.loads(result[7]) if result[7] else {},
            )

            return reading_list

    def list_reading_lists(self) -> List[ReadingList]:
        """Get all reading lists."""
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT id, name, description, tags, created_date, modified_date, is_public, metadata
                FROM reading_lists ORDER BY modified_date DESC
            """
            ).fetchall()

            lists = []
            for result in results:
                papers = self._get_papers_in_list(result[0])

                reading_list = ReadingList(
                    id=result[0],
                    name=result[1],
                    description=result[2] or "",
                    papers=papers,
                    tags=json.loads(result[3]) if result[3] else [],
                    created_date=datetime.fromisoformat(result[4]) if result[4] else datetime.now(),
                    modified_date=(
                        datetime.fromisoformat(result[5]) if result[5] else datetime.now()
                    ),
                    is_public=bool(result[6]),
                    metadata=json.loads(result[7]) if result[7] else {},
                )
                lists.append(reading_list)

            return lists

    def _get_papers_in_list(self, list_id: str) -> List[Paper]:
        """Get all papers in a reading list."""
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT p.arxiv_id, p.title, p.authors, p.abstract, p.categories,
                       p.submitted_date, p.url, p.pdf_url, p.tags, p.notes,
                       p.rating, p.read_status, p.added_date, p.last_accessed
                FROM papers p
                JOIN list_papers lp ON p.arxiv_id = lp.arxiv_id
                WHERE lp.list_id = ?
                ORDER BY lp.position, lp.added_date
            """,
                (list_id,),
            ).fetchall()

            papers = []
            for result in results:
                paper = Paper(
                    arxiv_id=result[0],
                    title=result[1],
                    authors=json.loads(result[2]) if result[2] else [],
                    abstract=result[3] or "",
                    categories=json.loads(result[4]) if result[4] else [],
                    submitted_date=datetime.fromisoformat(result[5]) if result[5] else None,
                    url=result[6] or "",
                    pdf_url=result[7] or "",
                    tags=json.loads(result[8]) if result[8] else [],
                    notes=result[9] or "",
                    rating=result[10],
                    read_status=result[11] or "unread",
                    added_date=datetime.fromisoformat(result[12]) if result[12] else datetime.now(),
                    last_accessed=datetime.fromisoformat(result[13]) if result[13] else None,
                )
                papers.append(paper)

            return papers

    def add_paper_to_list(self, list_id: str, paper: Paper, position: Optional[int] = None) -> bool:
        """Add a paper to a reading list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert or update paper
                conn.execute(
                    """
                    INSERT OR REPLACE INTO papers
                    (arxiv_id, title, authors, abstract, categories, submitted_date,
                     url, pdf_url, tags, notes, rating, read_status, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        paper.arxiv_id,
                        paper.title,
                        json.dumps(paper.authors),
                        paper.abstract,
                        json.dumps(paper.categories),
                        paper.submitted_date.isoformat() if paper.submitted_date else None,
                        paper.url,
                        paper.pdf_url,
                        json.dumps(paper.tags),
                        paper.notes,
                        paper.rating,
                        paper.read_status,
                        paper.last_accessed.isoformat() if paper.last_accessed else None,
                    ),
                )

                # Add to list
                if position is None:
                    # Get max position
                    max_pos = conn.execute(
                        "SELECT MAX(position) FROM list_papers WHERE list_id = ?",
                        (list_id,),
                    ).fetchone()[0]
                    position = (max_pos or 0) + 1

                conn.execute(
                    """
                    INSERT OR REPLACE INTO list_papers (list_id, arxiv_id, position)
                    VALUES (?, ?, ?)
                """,
                    (list_id, paper.arxiv_id, position),
                )

                # Update list modified date
                conn.execute(
                    """
                    UPDATE reading_lists SET modified_date = ? WHERE id = ?
                """,
                    (datetime.now().isoformat(), list_id),
                )

            logger.info(f"Added paper {paper.arxiv_id} to list {list_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add paper to list: {e}")
            return False

    def remove_paper_from_list(self, list_id: str, arxiv_id: str) -> bool:
        """Remove a paper from a reading list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    DELETE FROM list_papers WHERE list_id = ? AND arxiv_id = ?
                """,
                    (list_id, arxiv_id),
                )

                # Update list modified date
                conn.execute(
                    """
                    UPDATE reading_lists SET modified_date = ? WHERE id = ?
                """,
                    (datetime.now().isoformat(), list_id),
                )

            logger.info(f"Removed paper {arxiv_id} from list {list_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove paper from list: {e}")
            return False

    def update_paper_status(
        self, arxiv_id: str, status: str, notes: str = "", rating: Optional[int] = None
    ) -> bool:
        """Update a paper's reading status and metadata."""
        if status not in self.READ_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {self.READ_STATUSES}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                update_fields = ["read_status = ?", "last_accessed = ?"]
                values = [status, datetime.now().isoformat()]

                if notes:
                    update_fields.append("notes = ?")
                    values.append(notes)

                if rating is not None:
                    if not 1 <= rating <= 5:
                        raise ValueError("Rating must be between 1 and 5")
                    update_fields.append("rating = ?")
                    values.append(rating)

                values.append(arxiv_id)

                conn.execute(
                    f"""
                    UPDATE papers SET {", ".join(update_fields)} WHERE arxiv_id = ?
                """,
                    values,
                )

            logger.info(f"Updated paper {arxiv_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update paper status: {e}")
            return False

    def search_papers(
        self,
        query: str,
        list_id: Optional[str] = None,
        status: Optional[str] = None,
        tags: List[str] = None,
    ) -> List[Paper]:
        """Search papers across lists or within a specific list."""
        with sqlite3.connect(self.db_path) as conn:
            base_query = """
                SELECT DISTINCT p.arxiv_id, p.title, p.authors, p.abstract, p.categories,
                       p.submitted_date, p.url, p.pdf_url, p.tags, p.notes,
                       p.rating, p.read_status, p.added_date, p.last_accessed
                FROM papers p
            """

            conditions = []
            values = []

            if list_id:
                base_query += " JOIN list_papers lp ON p.arxiv_id = lp.arxiv_id"
                conditions.append("lp.list_id = ?")
                values.append(list_id)

            if query:
                conditions.append("(p.title LIKE ? OR p.abstract LIKE ? OR p.notes LIKE ?)")
                search_term = f"%{query}%"
                values.extend([search_term, search_term, search_term])

            if status:
                conditions.append("p.read_status = ?")
                values.append(status)

            if tags:
                # Search for papers containing any of the specified tags
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("p.tags LIKE ?")
                    values.append(f"%{tag}%")

                if tag_conditions:
                    conditions.append(f"({' OR '.join(tag_conditions)})")

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            base_query += " ORDER BY p.last_accessed DESC, p.added_date DESC"

            results = conn.execute(base_query, values).fetchall()

            papers = []
            for result in results:
                paper = Paper(
                    arxiv_id=result[0],
                    title=result[1],
                    authors=json.loads(result[2]) if result[2] else [],
                    abstract=result[3] or "",
                    categories=json.loads(result[4]) if result[4] else [],
                    submitted_date=datetime.fromisoformat(result[5]) if result[5] else None,
                    url=result[6] or "",
                    pdf_url=result[7] or "",
                    tags=json.loads(result[8]) if result[8] else [],
                    notes=result[9] or "",
                    rating=result[10],
                    read_status=result[11] or "unread",
                    added_date=datetime.fromisoformat(result[12]) if result[12] else datetime.now(),
                    last_accessed=datetime.fromisoformat(result[13]) if result[13] else None,
                )
                papers.append(paper)

            return papers

    def get_reading_statistics(
        self, list_id: Optional[str] = None, days: int = 30
    ) -> ReadingStatistics:
        """Generate reading statistics and analytics."""
        with sqlite3.connect(self.db_path) as conn:
            base_query = "FROM papers p"
            where_clause = ""
            values = []

            if list_id:
                base_query += " JOIN list_papers lp ON p.arxiv_id = lp.arxiv_id"
                where_clause = " WHERE lp.list_id = ?"
                values.append(list_id)

            # Count papers by status
            status_counts = {}
            for status in self.READ_STATUSES:
                count = conn.execute(
                    f"""
                    SELECT COUNT(*) {base_query} {where_clause}
                    {"AND" if where_clause else "WHERE"} p.read_status = ?
                """,
                    values + [status],
                ).fetchone()[0]
                status_counts[status] = count

            total_papers = sum(status_counts.values())

            # Calculate time spent (mock calculation - would need actual tracking)
            total_time = timedelta(hours=status_counts["read"] * 2)  # Assume 2 hours per paper
            avg_time = total_time / max(status_counts["read"], 1)

            # Get favorite categories
            category_results = conn.execute(
                f"""
                SELECT p.categories {base_query} {where_clause}
                {"AND" if where_clause else "WHERE"} p.categories IS NOT NULL
            """,
                values,
            ).fetchall()

            all_categories = []
            for result in category_results:
                categories = json.loads(result[0]) if result[0] else []
                all_categories.extend(categories)

            category_counts = Counter(all_categories)
            favorite_categories = [cat for cat, _ in category_counts.most_common(5)]

            # Get top authors
            author_results = conn.execute(
                f"""
                SELECT p.authors {base_query} {where_clause}
                {"AND" if where_clause else "WHERE"} p.authors IS NOT NULL
            """,
                values,
            ).fetchall()

            all_authors = []
            for result in author_results:
                authors = json.loads(result[0]) if result[0] else []
                all_authors.extend(authors)

            author_counts = Counter(all_authors)
            top_authors = [author for author, _ in author_counts.most_common(5)]

            # Calculate reading streak (simplified)
            recent_reads = conn.execute(
                f"""
                SELECT COUNT(*) {base_query} {where_clause}
                {"AND" if where_clause else "WHERE"} p.read_status = 'read'
                AND p.last_accessed >= datetime('now', '-{days} days')
            """,
                values,
            ).fetchone()[0]

            reading_streak = min(recent_reads, days)

            # Papers per month (last 6 months)
            papers_per_month = {}
            for i in range(6):
                month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
                month_key = month_start.strftime("%Y-%m")

                count = conn.execute(
                    f"""
                    SELECT COUNT(*) {base_query} {where_clause}
                    {"AND" if where_clause else "WHERE"} p.added_date >= ?
                    AND p.added_date < ?
                """,
                    values
                    + [
                        month_start.isoformat(),
                        (month_start + timedelta(days=32)).replace(day=1).isoformat(),
                    ],
                ).fetchone()[0]

                papers_per_month[month_key] = count

            return ReadingStatistics(
                total_papers=total_papers,
                read_papers=status_counts["read"],
                reading_papers=status_counts["reading"],
                unread_papers=status_counts["unread"],
                total_time_spent=total_time,
                average_time_per_paper=avg_time,
                favorite_categories=favorite_categories,
                reading_streak=reading_streak,
                papers_per_month=papers_per_month,
                top_authors=top_authors,
            )

    def export_reading_list(self, list_id: str, output_path: str, format: str = "json") -> bool:
        """Export a reading list to file."""
        try:
            reading_list = self.get_reading_list(list_id)
            if not reading_list:
                logger.error(f"Reading list {list_id} not found")
                return False

            output_file = Path(output_path)

            if format == "json":
                # Convert to JSON-serializable format
                data = asdict(reading_list)

                # Convert datetime objects to strings
                def serialize_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return obj

                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2, default=serialize_datetime)

            elif format == "csv":
                import csv

                with open(output_file, "w", newline="") as f:
                    fieldnames = [
                        "arxiv_id",
                        "title",
                        "authors",
                        "abstract",
                        "categories",
                        "read_status",
                        "rating",
                        "notes",
                        "tags",
                        "added_date",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for paper in reading_list.papers:
                        row = {
                            "arxiv_id": paper.arxiv_id,
                            "title": paper.title,
                            "authors": ", ".join(paper.authors),
                            "abstract": paper.abstract,
                            "categories": ", ".join(paper.categories),
                            "read_status": paper.read_status,
                            "rating": paper.rating,
                            "notes": paper.notes,
                            "tags": ", ".join(paper.tags),
                            "added_date": paper.added_date.isoformat() if paper.added_date else "",
                        }
                        writer.writerow(row)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Exported reading list {list_id} to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export reading list: {e}")
            return False

    def import_reading_list(self, input_path: str, list_name: str) -> Optional[str]:
        """Import a reading list from file."""
        try:
            input_file = Path(input_path)

            if input_file.suffix == ".json":
                with open(input_file, "r") as f:
                    data = json.load(f)

                # Create new reading list
                reading_list = self.create_reading_list(
                    name=list_name,
                    description=data.get("description", ""),
                    tags=data.get("tags", []),
                )

                # Add papers
                for paper_data in data.get("papers", []):
                    paper = Paper(
                        arxiv_id=paper_data["arxiv_id"],
                        title=paper_data["title"],
                        authors=paper_data.get("authors", []),
                        abstract=paper_data.get("abstract", ""),
                        categories=paper_data.get("categories", []),
                        read_status=paper_data.get("read_status", "unread"),
                        rating=paper_data.get("rating"),
                        notes=paper_data.get("notes", ""),
                        tags=paper_data.get("tags", []),
                    )
                    self.add_paper_to_list(reading_list.id, paper)

                logger.info(
                    f"Imported reading list {list_name} with {len(data.get('papers', []))} papers"
                )
                return reading_list.id

            else:
                raise ValueError(f"Unsupported import format: {input_file.suffix}")

        except Exception as e:
            logger.error(f"Failed to import reading list: {e}")
            return None

    def delete_reading_list(self, list_id: str) -> bool:
        """Delete a reading list (but keep papers)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM list_papers WHERE list_id = ?", (list_id,))
                conn.execute("DELETE FROM reading_progress WHERE list_id = ?", (list_id,))
                conn.execute("DELETE FROM reading_lists WHERE id = ?", (list_id,))

            logger.info(f"Deleted reading list {list_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete reading list: {e}")
            return False


# Convenience functions
def create_reading_list_manager(cache_dir: Optional[str] = None) -> ReadingListManager:
    """Create a configured ReadingListManager instance."""
    return ReadingListManager(cache_dir=cache_dir)


def quick_bookmark_paper(arxiv_id: str, title: str, list_name: str = "Default") -> bool:
    """Quick paper bookmarking for simple use cases."""
    manager = ReadingListManager()

    # Get or create default list
    lists = manager.list_reading_lists()
    target_list = None

    for reading_list in lists:
        if reading_list.name == list_name:
            target_list = reading_list
            break

    if not target_list:
        target_list = manager.create_reading_list(list_name, "Default reading list")

    # Create paper
    paper = Paper(arxiv_id=arxiv_id, title=title)
    return manager.add_paper_to_list(target_list.id, paper)
