"""
Search analytics for tracking query patterns, popular searches, and usage statistics.
Extends the existing metrics system with specialized search tracking.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

from .logging import structured_logger
from .metrics import MetricsCollector


@dataclass
class SearchQuery:
    """Represents a search query with metadata."""

    query: str
    timestamp: datetime
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    date_range: Optional[Tuple[Optional[str], Optional[str]]] = None
    results_count: int = 0
    response_time: float = 0.0
    user_id: Optional[str] = None
    success: bool = True


class SearchAnalytics:
    """Analytics engine for tracking and analyzing search patterns."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize search analytics with optional database path."""
        self.logger = structured_logger(__name__)
        self.metrics = MetricsCollector()

        # Use default cache directory if not specified
        if db_path is None:
            cache_dir = Path.home() / ".cache" / "arxiv-mcp"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "search_analytics.db"

        self.db_path = db_path
        self._init_database()

        # In-memory caches for performance
        self._query_cache = []
        self._popular_terms = Counter()
        self._category_stats = defaultdict(int)

    def _init_database(self):
        """Initialize SQLite database for persistent analytics storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS search_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        categories TEXT,
                        authors TEXT,
                        date_range TEXT,
                        results_count INTEGER DEFAULT 0,
                        response_time REAL DEFAULT 0.0,
                        user_id TEXT,
                        success BOOLEAN DEFAULT TRUE
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS popular_terms (
                        term TEXT PRIMARY KEY,
                        count INTEGER DEFAULT 1,
                        last_seen TEXT
                    )
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON search_queries(timestamp)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query ON search_queries(query)
                """)

            self.logger.info(f"Search analytics database initialized at {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize analytics database: {e}")
            raise

    def track_search(self, search_query: SearchQuery):
        """Track a search query with full metadata."""
        try:
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO search_queries 
                    (query, timestamp, categories, authors, date_range, results_count, 
                     response_time, user_id, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        search_query.query,
                        search_query.timestamp.isoformat(),
                        json.dumps(search_query.categories)
                        if search_query.categories
                        else None,
                        json.dumps(search_query.authors)
                        if search_query.authors
                        else None,
                        json.dumps(search_query.date_range)
                        if search_query.date_range
                        else None,
                        search_query.results_count,
                        search_query.response_time,
                        search_query.user_id,
                        search_query.success,
                    ),
                )

            # Update in-memory caches
            self._query_cache.append(search_query)
            self._update_popular_terms(search_query.query)

            if search_query.categories:
                for category in search_query.categories:
                    self._category_stats[category] += 1

            # Update metrics
            self.metrics.increment_counter("search_queries_total")
            if search_query.success:
                self.metrics.increment_counter("search_queries_successful")
            else:
                self.metrics.increment_counter("search_queries_failed")

            self.metrics.set_gauge("avg_response_time", search_query.response_time)
            self.metrics.set_gauge("avg_results_count", search_query.results_count)

            self.logger.debug(f"Tracked search query: {search_query.query[:50]}...")

        except Exception as e:
            self.logger.error(f"Failed to track search query: {e}")

    def _update_popular_terms(self, query: str):
        """Extract and update popular search terms."""
        # Simple term extraction (can be enhanced with NLP)
        terms = query.lower().split()
        terms = [term.strip('.,!?;:"()[]{}') for term in terms if len(term) > 2]

        for term in terms:
            self._popular_terms[term] += 1

            # Update database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO popular_terms (term, count, last_seen)
                        VALUES (?, COALESCE((SELECT count FROM popular_terms WHERE term = ?) + 1, 1), ?)
                    """,
                        (term, term, datetime.now().isoformat()),
                    )
            except Exception as e:
                self.logger.warning(f"Failed to update popular term {term}: {e}")

    def get_query_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Get query pattern analysis for the specified number of days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                # Query frequency over time
                queries = conn.execute(
                    """
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM search_queries 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """,
                    (cutoff_date.isoformat(),),
                ).fetchall()

                # Most common queries
                common_queries = conn.execute(
                    """
                    SELECT query, COUNT(*) as count
                    FROM search_queries 
                    WHERE timestamp >= ?
                    GROUP BY query
                    ORDER BY count DESC
                    LIMIT 20
                """,
                    (cutoff_date.isoformat(),),
                ).fetchall()

                # Success rate
                success_stats = conn.execute(
                    """
                    SELECT success, COUNT(*) as count
                    FROM search_queries 
                    WHERE timestamp >= ?
                    GROUP BY success
                """,
                    (cutoff_date.isoformat(),),
                ).fetchall()

                # Average response time
                avg_response = conn.execute(
                    """
                    SELECT AVG(response_time) as avg_time
                    FROM search_queries 
                    WHERE timestamp >= ? AND response_time > 0
                """,
                    (cutoff_date.isoformat(),),
                ).fetchone()

            return {
                "query_frequency": [
                    {"date": row[0], "count": row[1]} for row in queries
                ],
                "common_queries": [
                    {"query": row[0], "count": row[1]} for row in common_queries
                ],
                "success_rate": {
                    "successful": next((row[1] for row in success_stats if row[0]), 0),
                    "failed": next((row[1] for row in success_stats if not row[0]), 0),
                },
                "avg_response_time": avg_response[0]
                if avg_response and avg_response[0]
                else 0.0,
                "analysis_period_days": days,
            }

        except Exception as e:
            self.logger.error(f"Failed to get query patterns: {e}")
            return {}

    def get_popular_searches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most popular search terms."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                results = conn.execute(
                    """
                    SELECT term, count, last_seen
                    FROM popular_terms
                    ORDER BY count DESC
                    LIMIT ?
                """,
                    (limit,),
                ).fetchall()

                return [
                    {"term": row[0], "count": row[1], "last_seen": row[2]}
                    for row in results
                ]

        except Exception as e:
            self.logger.error(f"Failed to get popular searches: {e}")
            return []

    def get_usage_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                # Total queries
                total_queries = conn.execute(
                    """
                    SELECT COUNT(*) FROM search_queries WHERE timestamp >= ?
                """,
                    (cutoff_date.isoformat(),),
                ).fetchone()[0]

                # Unique queries
                unique_queries = conn.execute(
                    """
                    SELECT COUNT(DISTINCT query) FROM search_queries WHERE timestamp >= ?
                """,
                    (cutoff_date.isoformat(),),
                ).fetchone()[0]

                # Peak hour analysis
                hourly_stats = conn.execute(
                    """
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM search_queries 
                    WHERE timestamp >= ?
                    GROUP BY hour
                    ORDER BY count DESC
                """,
                    (cutoff_date.isoformat(),),
                ).fetchall()

                # Category usage
                category_usage = defaultdict(int)
                category_queries = conn.execute(
                    """
                    SELECT categories FROM search_queries 
                    WHERE timestamp >= ? AND categories IS NOT NULL
                """,
                    (cutoff_date.isoformat(),),
                ).fetchall()

                for row in category_queries:
                    try:
                        categories = json.loads(row[0])
                        for cat in categories:
                            category_usage[cat] += 1
                    except json.JSONDecodeError:
                        continue

            return {
                "total_queries": total_queries,
                "unique_queries": unique_queries,
                "repeat_rate": (total_queries - unique_queries) / total_queries
                if total_queries > 0
                else 0,
                "peak_hours": [
                    {"hour": row[0], "count": row[1]} for row in hourly_stats[:5]
                ],
                "category_usage": dict(category_usage),
                "analysis_period_days": days,
            }

        except Exception as e:
            self.logger.error(f"Failed to get usage statistics: {e}")
            return {}

    def get_trending_queries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get trending queries in the specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                trending = conn.execute(
                    """
                    SELECT query, COUNT(*) as recent_count,
                           AVG(results_count) as avg_results,
                           AVG(response_time) as avg_time
                    FROM search_queries 
                    WHERE timestamp >= ?
                    GROUP BY query
                    HAVING recent_count >= 2
                    ORDER BY recent_count DESC, avg_results DESC
                    LIMIT 20
                """,
                    (cutoff_time.isoformat(),),
                ).fetchall()

                return [
                    {
                        "query": row[0],
                        "frequency": row[1],
                        "avg_results": row[2],
                        "avg_response_time": row[3],
                    }
                    for row in trending
                ]

        except Exception as e:
            self.logger.error(f"Failed to get trending queries: {e}")
            return []

    def export_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Export comprehensive analytics data."""
        return {
            "query_patterns": self.get_query_patterns(days),
            "popular_searches": self.get_popular_searches(),
            "usage_statistics": self.get_usage_statistics(days),
            "trending_queries": self.get_trending_queries(),
            "export_timestamp": datetime.now().isoformat(),
        }


# Global analytics instance
_analytics_instance = None


def get_search_analytics() -> SearchAnalytics:
    """Get the global search analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = SearchAnalytics()
    return _analytics_instance
