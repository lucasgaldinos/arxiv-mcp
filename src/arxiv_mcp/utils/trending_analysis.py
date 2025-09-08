#!/usr/bin/env python3
"""
Trending Analysis System for ArXiv MCP

This module provides trending analysis and popularity tracking capabilities
for research papers, including download metrics, citation trends, and topic analysis.
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import math
import statistics

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class TrendingPaper:
    """Represents a trending paper with metrics."""

    arxiv_id: str
    title: str
    authors: List[str]
    categories: List[str]
    submitted_date: datetime
    trend_score: float
    download_count: int = 0
    citation_count: int = 0
    view_count: int = 0
    social_mentions: int = 0
    velocity: float = 0.0  # Rate of change
    rank_change: int = 0  # Position change from previous period
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendingCategory:
    """Represents a trending research category."""

    category: str
    paper_count: int
    total_downloads: int
    average_citations: float
    trend_score: float
    growth_rate: float
    top_papers: List[str] = field(default_factory=list)


@dataclass
class TrendingKeyword:
    """Represents a trending keyword or topic."""

    keyword: str
    frequency: int
    papers_count: int
    trend_score: float
    related_terms: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)


@dataclass
class TrendingStats:
    """Overall trending statistics."""

    total_papers_analyzed: int
    trending_threshold: float
    top_categories: List[TrendingCategory]
    top_keywords: List[TrendingKeyword]
    viral_papers: List[TrendingPaper]  # Papers with exceptional growth
    emerging_topics: List[str]
    analysis_date: datetime = field(default_factory=datetime.now)


class TrendingAnalyzer:
    """
    Comprehensive trending analysis system for research papers.

    Features:
    - Download and view tracking
    - Citation trend analysis
    - Category popularity metrics
    - Keyword trending detection
    - Viral paper identification
    - Emerging topic discovery
    - Time-based trend analysis
    - Comparative metrics
    """

    # Scoring weights for trend calculation
    TREND_WEIGHTS = {
        "downloads": 0.3,
        "citations": 0.25,
        "views": 0.2,
        "social": 0.15,
        "recency": 0.1,
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the trending analyzer."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "trending_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "trending.db"
        self._init_database()

        logger.info(f"TrendingAnalyzer initialized with cache: {self.cache_dir}")

    def _init_database(self) -> None:
        """Initialize SQLite database for trending data."""
        with sqlite3.connect(self.db_path) as conn:
            # Paper metrics table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_metrics (
                    arxiv_id TEXT,
                    date DATE,
                    download_count INTEGER DEFAULT 0,
                    citation_count INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    social_mentions INTEGER DEFAULT 0,
                    trend_score REAL DEFAULT 0.0,
                    rank_position INTEGER,
                    PRIMARY KEY (arxiv_id, date)
                )
            """
            )

            # Category trends table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS category_trends (
                    category TEXT,
                    date DATE,
                    paper_count INTEGER DEFAULT 0,
                    total_downloads INTEGER DEFAULT 0,
                    total_citations INTEGER DEFAULT 0,
                    trend_score REAL DEFAULT 0.0,
                    growth_rate REAL DEFAULT 0.0,
                    PRIMARY KEY (category, date)
                )
            """
            )

            # Keyword trends table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_trends (
                    keyword TEXT,
                    date DATE,
                    frequency INTEGER DEFAULT 0,
                    papers_count INTEGER DEFAULT 0,
                    trend_score REAL DEFAULT 0.0,
                    related_terms TEXT,
                    categories TEXT,
                    PRIMARY KEY (keyword, date)
                )
            """
            )

            # Trending snapshots table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trending_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    snapshot_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT
                )
            """
            )

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON paper_metrics(date)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_score ON paper_metrics(trend_score)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category_date ON category_trends(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_keyword_date ON keyword_trends(date)")

    def record_paper_metrics(
        self, arxiv_id: str, metrics: Dict[str, int], date: datetime = None
    ) -> None:
        """Record metrics for a paper."""
        if date is None:
            date = datetime.now().date()

        download_count = metrics.get("downloads", 0)
        citation_count = metrics.get("citations", 0)
        view_count = metrics.get("views", 0)
        social_mentions = metrics.get("social", 0)

        # Calculate trend score
        trend_score = self._calculate_trend_score(metrics, date)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO paper_metrics
                (arxiv_id, date, download_count, citation_count, view_count,
                 social_mentions, trend_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    arxiv_id,
                    date.isoformat(),
                    download_count,
                    citation_count,
                    view_count,
                    social_mentions,
                    trend_score,
                ),
            )

        logger.debug(f"Recorded metrics for {arxiv_id}: score {trend_score:.2f}")

    def _calculate_trend_score(self, metrics: Dict[str, int], date: datetime) -> float:
        """Calculate trending score for a paper."""
        # Normalize metrics (using log scale for large numbers)
        downloads = math.log1p(metrics.get("downloads", 0))
        citations = math.log1p(metrics.get("citations", 0))
        views = math.log1p(metrics.get("views", 0))
        social = math.log1p(metrics.get("social", 0))

        # Recency bonus (papers from last 30 days get bonus)
        days_old = (datetime.now().date() - date).days
        recency = max(0, 1 - (days_old / 30))

        # Weighted score
        score = (
            downloads * self.TREND_WEIGHTS["downloads"]
            + citations * self.TREND_WEIGHTS["citations"]
            + views * self.TREND_WEIGHTS["views"]
            + social * self.TREND_WEIGHTS["social"]
            + recency * self.TREND_WEIGHTS["recency"]
        )

        return round(score, 3)

    def get_trending_papers(
        self, limit: int = 20, days: int = 7, category: str = None
    ) -> List[TrendingPaper]:
        """Get currently trending papers."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Base query for trending papers
            query = """
                SELECT
                    pm.arxiv_id,
                    AVG(pm.trend_score) as avg_score,
                    MAX(pm.download_count) as max_downloads,
                    MAX(pm.citation_count) as max_citations,
                    MAX(pm.view_count) as max_views,
                    MAX(pm.social_mentions) as max_social
                FROM paper_metrics pm
                WHERE pm.date >= ? AND pm.date <= ?
            """
            params = [start_date.isoformat(), end_date.isoformat()]

            # Add category filter if specified
            if category:
                # This would require joining with a papers table that has category info
                # For now, we'll proceed without category filtering
                pass

            query += """
                GROUP BY pm.arxiv_id
                HAVING AVG(pm.trend_score) > 0
                ORDER BY avg_score DESC
                LIMIT ?
            """
            params.append(limit)

            results = conn.execute(query, params).fetchall()

            trending_papers = []
            for i, result in enumerate(results):
                arxiv_id = result[0]
                avg_score = result[1]

                # Calculate velocity (rate of change)
                velocity = self._calculate_velocity(arxiv_id, days)

                # Get rank change
                rank_change = self._calculate_rank_change(arxiv_id, days)

                # Create trending paper (mock data for missing fields)
                trending_paper = TrendingPaper(
                    arxiv_id=arxiv_id,
                    title=f"Paper {arxiv_id}",  # Would fetch from papers table
                    authors=[],  # Would fetch from papers table
                    categories=[],  # Would fetch from papers table
                    submitted_date=datetime.now() - timedelta(days=30),  # Mock
                    trend_score=avg_score,
                    download_count=result[2],
                    citation_count=result[3],
                    view_count=result[4],
                    social_mentions=result[5],
                    velocity=velocity,
                    rank_change=rank_change,
                )
                trending_papers.append(trending_paper)

            return trending_papers

    def _calculate_velocity(self, arxiv_id: str, days: int) -> float:
        """Calculate the rate of change in trending score."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        mid_date = start_date + timedelta(days=days // 2)

        with sqlite3.connect(self.db_path) as conn:
            # Get average scores for first and second half of period
            first_half = conn.execute(
                """
                SELECT AVG(trend_score) FROM paper_metrics
                WHERE arxiv_id = ? AND date >= ? AND date < ?
            """,
                (arxiv_id, start_date.isoformat(), mid_date.isoformat()),
            ).fetchone()[0]

            second_half = conn.execute(
                """
                SELECT AVG(trend_score) FROM paper_metrics
                WHERE arxiv_id = ? AND date >= ? AND date <= ?
            """,
                (arxiv_id, mid_date.isoformat(), end_date.isoformat()),
            ).fetchone()[0]

            if first_half and second_half and first_half > 0:
                velocity = (second_half - first_half) / first_half
                return round(velocity, 3)

            return 0.0

    def _calculate_rank_change(self, arxiv_id: str, days: int) -> int:
        """Calculate change in ranking position."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Get ranks for different periods
            # This is a simplified calculation
            current_rank = conn.execute(
                """
                SELECT COUNT(*) + 1 FROM paper_metrics pm1
                WHERE pm1.date = ? AND pm1.trend_score > (
                    SELECT trend_score FROM paper_metrics pm2
                    WHERE pm2.arxiv_id = ? AND pm2.date = ?
                )
            """,
                (end_date.isoformat(), arxiv_id, end_date.isoformat()),
            ).fetchone()[0]

            previous_rank = conn.execute(
                """
                SELECT COUNT(*) + 1 FROM paper_metrics pm1
                WHERE pm1.date = ? AND pm1.trend_score > (
                    SELECT trend_score FROM paper_metrics pm2
                    WHERE pm2.arxiv_id = ? AND pm2.date = ?
                )
            """,
                (start_date.isoformat(), arxiv_id, start_date.isoformat()),
            ).fetchone()[0]

            return previous_rank - current_rank

    def analyze_category_trends(self, days: int = 30) -> List[TrendingCategory]:
        """Analyze trending categories."""
        # Mock category analysis (would need actual category data)
        categories = ["cs.AI", "cs.LG", "physics.comp-ph", "math.OC", "stat.ML"]
        trending_categories = []

        for category in categories:
            # Calculate mock metrics
            paper_count = 50 + len(category) * 10  # Mock
            total_downloads = paper_count * 25  # Mock
            average_citations = 5.5  # Mock

            trend_score = self._calculate_category_trend_score(category, days)
            growth_rate = 0.15  # Mock 15% growth

            trending_category = TrendingCategory(
                category=category,
                paper_count=paper_count,
                total_downloads=total_downloads,
                average_citations=average_citations,
                trend_score=trend_score,
                growth_rate=growth_rate,
                top_papers=[f"{category}-paper-{i}" for i in range(3)],
            )
            trending_categories.append(trending_category)

        # Sort by trend score
        trending_categories.sort(key=lambda x: x.trend_score, reverse=True)
        return trending_categories

    def _calculate_category_trend_score(self, category: str, days: int) -> float:
        """Calculate trend score for a category."""
        # Mock calculation - would analyze actual category metrics
        base_score = 0.5
        category_multiplier = {"cs.AI": 1.5, "cs.LG": 1.4, "physics.comp-ph": 1.2}.get(
            category, 1.0
        )
        return round(base_score * category_multiplier, 3)

    def analyze_keyword_trends(self, limit: int = 20, days: int = 14) -> List[TrendingKeyword]:
        """Analyze trending keywords and topics."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT
                    keyword,
                    SUM(frequency) as total_frequency,
                    COUNT(DISTINCT date) as appearances,
                    AVG(trend_score) as avg_score,
                    related_terms,
                    categories
                FROM keyword_trends
                WHERE date >= ? AND date <= ?
                GROUP BY keyword
                HAVING total_frequency > 5
                ORDER BY avg_score DESC, total_frequency DESC
                LIMIT ?
            """,
                (start_date.isoformat(), end_date.isoformat(), limit),
            ).fetchall()

            trending_keywords = []
            for result in results:
                keyword = result[0]
                frequency = result[1]
                papers_count = result[2]  # Approximation
                trend_score = result[3] or 0.0
                related_terms = json.loads(result[4]) if result[4] else []
                categories = json.loads(result[5]) if result[5] else []

                trending_keyword = TrendingKeyword(
                    keyword=keyword,
                    frequency=frequency,
                    papers_count=papers_count,
                    trend_score=trend_score,
                    related_terms=related_terms,
                    categories=categories,
                )
                trending_keywords.append(trending_keyword)

            return trending_keywords

    def record_keyword_trend(
        self,
        keyword: str,
        frequency: int,
        related_terms: List[str] = None,
        categories: List[str] = None,
        date: datetime = None,
    ) -> None:
        """Record keyword trend data."""
        if date is None:
            date = datetime.now().date()

        related_terms = related_terms or []
        categories = categories or []

        # Calculate trend score for keyword
        trend_score = self._calculate_keyword_trend_score(keyword, frequency)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO keyword_trends
                (keyword, date, frequency, papers_count, trend_score, related_terms, categories)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    keyword,
                    date.isoformat(),
                    frequency,
                    frequency,  # Using frequency as papers count approximation
                    trend_score,
                    json.dumps(related_terms),
                    json.dumps(categories),
                ),
            )

    def _calculate_keyword_trend_score(self, keyword: str, frequency: int) -> float:
        """Calculate trend score for a keyword."""
        # Base score from frequency
        base_score = math.log1p(frequency) / 10

        # Bonus for certain high-impact keywords
        impact_keywords = {
            "neural,ai,machine learning,deep learning": 1.5,
            "quantum,blockchain,transformer": 1.3,
            "covid,climate,sustainability": 1.4,
        }

        multiplier = 1.0
        for keywords, mult in impact_keywords.items():
            if any(kw in keyword.lower() for kw in keywords.split(", ")):
                multiplier = mult
                break

        return round(base_score * multiplier, 3)

    def identify_viral_papers(
        self, threshold_multiplier: float = 3.0, days: int = 7
    ) -> List[TrendingPaper]:
        """Identify papers with exceptional growth (viral papers)."""
        trending_papers = self.get_trending_papers(limit=100, days=days)

        if not trending_papers:
            return []

        # Calculate average trend score
        avg_score = statistics.mean(paper.trend_score for paper in trending_papers)
        threshold = avg_score * threshold_multiplier

        # Filter viral papers
        viral_papers = [
            paper
            for paper in trending_papers
            if paper.trend_score > threshold and paper.velocity > 0.5
        ]

        # Sort by trend score and velocity
        viral_papers.sort(key=lambda x: (x.trend_score, x.velocity), reverse=True)

        logger.info(f"Identified {len(viral_papers)} viral papers (threshold: {threshold:.2f})")
        return viral_papers

    def detect_emerging_topics(self, days: int = 30, growth_threshold: float = 2.0) -> List[str]:
        """Detect emerging topics based on keyword growth."""
        current_keywords = self.analyze_keyword_trends(limit=50, days=days // 2)
        past_keywords = self.analyze_keyword_trends(limit=50, days=days)

        # Create frequency maps
        current_freq = {kw.keyword: kw.frequency for kw in current_keywords}
        past_freq = {kw.keyword: kw.frequency for kw in past_keywords}

        emerging_topics = []

        for keyword in current_freq:
            current_count = current_freq[keyword]
            past_count = past_freq.get(keyword, 0)

            # Calculate growth rate
            if past_count > 0:
                growth_rate = current_count / past_count
            else:
                growth_rate = float("inf") if current_count > 0 else 0

            # Check if it's emerging
            if growth_rate >= growth_threshold and current_count >= 5:
                emerging_topics.append(keyword)

        # Sort by current frequency
        emerging_topics.sort(key=lambda x: current_freq[x], reverse=True)

        logger.info(f"Detected {len(emerging_topics)} emerging topics")
        return emerging_topics[:10]  # Return top 10

    def generate_trending_report(self, days: int = 7) -> TrendingStats:
        """Generate a comprehensive trending analysis report."""
        # Get trending papers
        trending_papers = self.get_trending_papers(limit=20, days=days)
        total_papers = len(trending_papers)

        # Calculate trending threshold
        if trending_papers:
            trending_threshold = statistics.median(paper.trend_score for paper in trending_papers)
        else:
            trending_threshold = 0.0

        # Get trending categories
        top_categories = self.analyze_category_trends(days=days)[:10]

        # Get trending keywords
        top_keywords = self.analyze_keyword_trends(limit=15, days=days)

        # Identify viral papers
        viral_papers = self.identify_viral_papers(days=days)

        # Detect emerging topics
        emerging_topics = self.detect_emerging_topics(days=days)

        return TrendingStats(
            total_papers_analyzed=total_papers,
            trending_threshold=trending_threshold,
            top_categories=top_categories,
            top_keywords=top_keywords,
            viral_papers=viral_papers,
            emerging_topics=emerging_topics,
        )

    def save_trending_snapshot(
        self, snapshot_type: str, data: Dict[str, Any], date: datetime = None
    ) -> None:
        """Save a snapshot of trending data."""
        if date is None:
            date = datetime.now().date()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO trending_snapshots (date, snapshot_type, data, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    date.isoformat(),
                    snapshot_type,
                    json.dumps(data, default=str),
                    json.dumps({"created_at": datetime.now().isoformat()}),
                ),
            )

    def get_historical_trends(self, arxiv_id: str, days: int = 30) -> List[Tuple[datetime, float]]:
        """Get historical trend data for a paper."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute(
                """
                SELECT date, trend_score FROM paper_metrics
                WHERE arxiv_id = ? AND date >= ? AND date <= ?
                ORDER BY date
            """,
                (arxiv_id, start_date.isoformat(), end_date.isoformat()),
            ).fetchall()

            return [(datetime.fromisoformat(row[0]).date(), row[1]) for row in results]

    def compare_papers(self, arxiv_ids: List[str], days: int = 30) -> Dict[str, Dict[str, float]]:
        """Compare trending metrics between papers."""
        comparison = {}

        for arxiv_id in arxiv_ids:
            trends = self.get_historical_trends(arxiv_id, days)

            if trends:
                scores = [score for _, score in trends]
                comparison[arxiv_id] = {
                    "average_score": statistics.mean(scores),
                    "peak_score": max(scores),
                    "current_score": scores[-1] if scores else 0,
                    "volatility": statistics.stdev(scores) if len(scores) > 1 else 0,
                    "trend_direction": (
                        "up" if len(scores) > 1 and scores[-1] > scores[0] else "down"
                    ),
                }
            else:
                comparison[arxiv_id] = {
                    "average_score": 0,
                    "peak_score": 0,
                    "current_score": 0,
                    "volatility": 0,
                    "trend_direction": "unknown",
                }

        return comparison

    def export_trending_data(self, output_path: str, format: str = "json", days: int = 30) -> bool:
        """Export trending analysis data."""
        try:
            report = self.generate_trending_report(days=days)

            output_file = Path(output_path)

            if format == "json":
                # Convert to JSON-serializable format
                data = {
                    "analysis_date": report.analysis_date.isoformat(),
                    "total_papers_analyzed": report.total_papers_analyzed,
                    "trending_threshold": report.trending_threshold,
                    "top_categories": [
                        {
                            "category": cat.category,
                            "paper_count": cat.paper_count,
                            "trend_score": cat.trend_score,
                            "growth_rate": cat.growth_rate,
                        }
                        for cat in report.top_categories
                    ],
                    "top_keywords": [
                        {
                            "keyword": kw.keyword,
                            "frequency": kw.frequency,
                            "trend_score": kw.trend_score,
                        }
                        for kw in report.top_keywords
                    ],
                    "viral_papers": [
                        {
                            "arxiv_id": paper.arxiv_id,
                            "title": paper.title,
                            "trend_score": paper.trend_score,
                            "velocity": paper.velocity,
                        }
                        for paper in report.viral_papers
                    ],
                    "emerging_topics": report.emerging_topics,
                }

                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                import csv

                # Export papers data as CSV
                with open(output_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Type", "Name", "Score", "Frequency", "Additional"])

                    # Add categories
                    for cat in report.top_categories:
                        writer.writerow(
                            [
                                "Category",
                                cat.category,
                                cat.trend_score,
                                cat.paper_count,
                                cat.growth_rate,
                            ]
                        )

                    # Add keywords
                    for kw in report.top_keywords:
                        writer.writerow(["Keyword", kw.keyword, kw.trend_score, kw.frequency, ""])
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Exported trending data to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export trending data: {e}")
            return False


# Convenience functions
def create_trending_analyzer(cache_dir: Optional[str] = None) -> TrendingAnalyzer:
    """Create a configured TrendingAnalyzer instance."""
    return TrendingAnalyzer(cache_dir=cache_dir)


def quick_trending_check(arxiv_id: str, days: int = 7) -> float:
    """Quick trending score check for a paper."""
    analyzer = TrendingAnalyzer()
    trends = analyzer.get_historical_trends(arxiv_id, days)

    if trends:
        return trends[-1][1]  # Return latest score
    return 0.0
