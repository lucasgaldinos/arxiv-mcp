#!/usr/bin/env python3
"""
Paper Notifications System for ArXiv MCP

This module provides monitoring and notification capabilities for research papers,
including update tracking, version monitoring, and alert systems.
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import hashlib
from enum import Enum

from .logging import get_logger

logger = get_logger(__name__)


class NotificationType(Enum):
    """Types of notifications."""

    NEW_VERSION = "new_version"
    AUTHOR_UPDATE = "author_update"
    CATEGORY_UPDATE = "category_update"
    CITATION_MILESTONE = "citation_milestone"
    KEYWORD_MATCH = "keyword_match"
    READING_LIST_UPDATE = "reading_list_update"


@dataclass
class NotificationRule:
    """Defines a notification rule and its conditions."""

    id: str
    name: str
    notification_type: NotificationType
    conditions: Dict[str, Any]
    is_active: bool = True
    frequency: str = "immediate"  # immediate, daily, weekly
    last_triggered: Optional[datetime] = None
    created_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Represents a notification event."""

    id: str
    rule_id: str
    paper_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: str = "normal"  # low, normal, high, urgent
    is_read: bool = False
    created_date: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaperMonitor:
    """Monitors a specific paper for changes."""

    paper_id: str
    title: str
    authors: List[str]
    version: str
    last_check: datetime
    content_hash: str
    metadata_hash: str
    is_active: bool = True
    check_frequency: timedelta = field(default_factory=lambda: timedelta(days=1))
    created_date: datetime = field(default_factory=datetime.now)


@dataclass
class NotificationStats:
    """Statistics about notifications."""

    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    active_rules: int
    monitored_papers: int
    last_check: Optional[datetime]


class PaperNotificationSystem:
    """
    Comprehensive notification system for research papers.

    Features:
    - Monitor papers for new versions
    - Track author publications
    - Category-based alerts
    - Citation milestone tracking
    - Keyword matching notifications
    - Reading list updates
    - Customizable notification rules
    - Batch processing and scheduling
    """

    PRIORITY_LEVELS = ["low", "normal", "high", "urgent"]
    FREQUENCY_OPTIONS = ["immediate", "daily", "weekly"]

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the notification system."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "notification_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "notifications.db"
        self._init_database()

        # Notification handlers
        self._handlers: Dict[NotificationType, List[Callable]] = {
            notification_type: [] for notification_type in NotificationType
        }

        logger.info(f"PaperNotificationSystem initialized with cache: {self.cache_dir}")

    def _init_database(self) -> None:
        """Initialize SQLite database for persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            # Notification rules table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    frequency TEXT DEFAULT 'immediate',
                    last_triggered TIMESTAMP,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # Notifications table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    priority TEXT DEFAULT 'normal',
                    is_read BOOLEAN DEFAULT 0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT,
                    FOREIGN KEY (rule_id) REFERENCES notification_rules (id)
                )
            """
            )

            # Paper monitors table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_monitors (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    version TEXT,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    content_hash TEXT,
                    metadata_hash TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    check_frequency INTEGER DEFAULT 86400,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_rule ON notifications(rule_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_paper ON notifications(paper_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(is_read)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_monitors_active ON paper_monitors(is_active)"
            )

    def create_notification_rule(
        self,
        name: str,
        notification_type: NotificationType,
        conditions: Dict[str, Any],
        frequency: str = "immediate",
    ) -> NotificationRule:
        """Create a new notification rule."""
        if frequency not in self.FREQUENCY_OPTIONS:
            raise ValueError(
                f"Invalid frequency: {frequency}. Must be one of {self.FREQUENCY_OPTIONS}"
            )

        rule_id = str(uuid.uuid4())

        rule = NotificationRule(
            id=rule_id,
            name=name,
            notification_type=notification_type,
            conditions=conditions,
            frequency=frequency,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO notification_rules
                (id, name, notification_type, conditions, frequency, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    rule_id,
                    name,
                    notification_type.value,
                    json.dumps(conditions),
                    frequency,
                    json.dumps({}),
                ),
            )

        logger.info(f"Created notification rule: {name} ({rule_id})")
        return rule

    def get_notification_rules(self, active_only: bool = True) -> List[NotificationRule]:
        """Get all notification rules."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM notification_rules"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_date DESC"

            results = conn.execute(query).fetchall()

            rules = []
            for result in results:
                rule = NotificationRule(
                    id=result[0],
                    name=result[1],
                    notification_type=NotificationType(result[2]),
                    conditions=json.loads(result[3]),
                    is_active=bool(result[4]),
                    frequency=result[5],
                    last_triggered=datetime.fromisoformat(result[6]) if result[6] else None,
                    created_date=datetime.fromisoformat(result[7]) if result[7] else datetime.now(),
                    metadata=json.loads(result[8]) if result[8] else {},
                )
                rules.append(rule)

            return rules

    def add_paper_monitor(
        self,
        paper_id: str,
        title: str,
        authors: List[str],
        version: str = "1",
        check_frequency: timedelta = None,
    ) -> PaperMonitor:
        """Add a paper to monitoring."""
        if check_frequency is None:
            check_frequency = timedelta(days=1)

        # Calculate initial hashes
        content_hash = hashlib.md5(f"{title}{authors}{version}".encode()).hexdigest()
        metadata_hash = hashlib.md5(f"{title}{json.dumps(authors)}".encode()).hexdigest()

        monitor = PaperMonitor(
            paper_id=paper_id,
            title=title,
            authors=authors,
            version=version,
            last_check=datetime.now(),
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            check_frequency=check_frequency,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO paper_monitors
                (paper_id, title, authors, version, content_hash, metadata_hash, check_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    paper_id,
                    title,
                    json.dumps(authors),
                    version,
                    content_hash,
                    metadata_hash,
                    int(check_frequency.total_seconds()),
                ),
            )

        logger.info(f"Added paper monitor: {title} ({paper_id})")
        return monitor

    def check_paper_updates(
        self, paper_id: str, current_data: Dict[str, Any]
    ) -> List[Notification]:
        """Check for updates to a monitored paper."""
        notifications = []

        with sqlite3.connect(self.db_path) as conn:
            monitor_result = conn.execute(
                """
                SELECT title, authors, version, content_hash, metadata_hash
                FROM paper_monitors WHERE paper_id = ? AND is_active = 1
            """,
                (paper_id,),
            ).fetchone()

            if not monitor_result:
                return notifications

            (
                stored_title,
                stored_authors_json,
                stored_version,
                stored_content_hash,
                stored_metadata_hash,
            ) = monitor_result
            stored_authors = json.loads(stored_authors_json) if stored_authors_json else []

            # Check for version changes
            current_version = current_data.get("version", "1")
            if current_version != stored_version:
                notification = self._create_notification(
                    paper_id=paper_id,
                    title=current_data.get("title", stored_title),
                    notification_type=NotificationType.NEW_VERSION,
                    message=f"New version available: v{current_version} (was v{stored_version})",
                    priority="high",
                    data={
                        "old_version": stored_version,
                        "new_version": current_version,
                        "change_type": "version_update",
                    },
                )
                notifications.append(notification)

            # Check for metadata changes
            current_title = current_data.get("title", "")
            current_authors = current_data.get("authors", [])
            current_metadata_hash = hashlib.md5(
                f"{current_title}{json.dumps(current_authors)}".encode()
            ).hexdigest()

            if current_metadata_hash != stored_metadata_hash:
                changes = []
                if current_title != stored_title:
                    changes.append(f"Title changed: '{stored_title}' → '{current_title}'")
                if current_authors != stored_authors:
                    changes.append("Authors updated")

                if changes:
                    notification = self._create_notification(
                        paper_id=paper_id,
                        title=current_title or stored_title,
                        notification_type=NotificationType.AUTHOR_UPDATE,
                        message=f"Paper metadata updated: {'; '.join(changes)}",
                        priority="normal",
                        data={
                            "changes": changes,
                            "old_metadata": {
                                "title": stored_title,
                                "authors": stored_authors,
                            },
                            "new_metadata": {
                                "title": current_title,
                                "authors": current_authors,
                            },
                        },
                    )
                    notifications.append(notification)

            # Update monitor record
            conn.execute(
                """
                UPDATE paper_monitors
                SET title = ?, authors = ?, version = ?, content_hash = ?,
                    metadata_hash = ?, last_check = ?
                WHERE paper_id = ?
            """,
                (
                    current_title or stored_title,
                    json.dumps(current_authors),
                    current_version,
                    hashlib.md5(
                        f"{current_title}{current_authors}{current_version}".encode()
                    ).hexdigest(),
                    current_metadata_hash,
                    datetime.now().isoformat(),
                    paper_id,
                ),
            )

        return notifications

    def _create_notification(
        self,
        paper_id: str,
        title: str,
        notification_type: NotificationType,
        message: str,
        priority: str = "normal",
        data: Dict[str, Any] = None,
        rule_id: str = None,
    ) -> Notification:
        """Create and store a notification."""
        if priority not in self.PRIORITY_LEVELS:
            priority = "normal"

        notification_id = str(uuid.uuid4())
        rule_id = rule_id or "system"
        data = data or {}

        notification = Notification(
            id=notification_id,
            rule_id=rule_id,
            paper_id=paper_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            data=data,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO notifications
                (id, rule_id, paper_id, title, message, notification_type, priority, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    notification_id,
                    rule_id,
                    paper_id,
                    title,
                    message,
                    notification_type.value,
                    priority,
                    json.dumps(data),
                ),
            )

        # Trigger handlers
        self._trigger_handlers(notification)

        return notification

    def create_keyword_alert(self, keywords: List[str], name: str = None) -> NotificationRule:
        """Create a keyword-based alert rule."""
        name = name or f"Keyword Alert: {', '.join(keywords[:3])}"

        conditions = {
            "keywords": keywords,
            "match_type": "any",  # any, all
            "fields": ["title", "abstract"],  # fields to search
            "case_sensitive": False,
        }

        return self.create_notification_rule(
            name=name,
            notification_type=NotificationType.KEYWORD_MATCH,
            conditions=conditions,
            frequency="daily",
        )

    def create_author_alert(self, authors: List[str], name: str = None) -> NotificationRule:
        """Create an author-based alert rule."""
        name = name or f"Author Alert: {', '.join(authors[:2])}"

        conditions = {
            "authors": authors,
            "match_type": "any",
            "include_collaborations": True,
        }

        return self.create_notification_rule(
            name=name,
            notification_type=NotificationType.AUTHOR_UPDATE,
            conditions=conditions,
            frequency="immediate",
        )

    def create_category_alert(self, categories: List[str], name: str = None) -> NotificationRule:
        """Create a category-based alert rule."""
        name = name or f"Category Alert: {', '.join(categories)}"

        conditions = {
            "categories": categories,
            "match_type": "any",
            "subcategories": True,
        }

        return self.create_notification_rule(
            name=name,
            notification_type=NotificationType.CATEGORY_UPDATE,
            conditions=conditions,
            frequency="daily",
        )

    def check_keyword_matches(self, paper_data: Dict[str, Any]) -> List[Notification]:
        """Check if a paper matches any keyword alert rules."""
        notifications = []
        rules = [
            r
            for r in self.get_notification_rules()
            if r.notification_type == NotificationType.KEYWORD_MATCH
        ]

        for rule in rules:
            if self._should_trigger_rule(rule):
                keywords = rule.conditions.get("keywords", [])
                fields = rule.conditions.get("fields", ["title", "abstract"])
                case_sensitive = rule.conditions.get("case_sensitive", False)
                match_type = rule.conditions.get("match_type", "any")

                # Extract text to search
                text_to_search = ""
                for notification_field in fields:
                    if field in paper_data:
                        text_to_search += f" {paper_data[field]}"

                if not case_sensitive:
                    text_to_search = text_to_search.lower()
                    keywords = [kw.lower() for kw in keywords]

                # Check matches
                matches = []
                for keyword in keywords:
                    if keyword in text_to_search:
                        matches.append(keyword)

                # Determine if rule is triggered
                triggered = False
                if match_type == "any" and matches:
                    triggered = True
                elif match_type == "all" and len(matches) == len(keywords):
                    triggered = True

                if triggered:
                    notification = self._create_notification(
                        paper_id=paper_data.get("arxiv_id", ""),
                        title=paper_data.get("title", ""),
                        notification_type=NotificationType.KEYWORD_MATCH,
                        message=f"Keywords matched: {', '.join(matches)}",
                        priority="normal",
                        data={
                            "matched_keywords": matches,
                            "rule_name": rule.name,
                            "fields_searched": fields,
                        },
                        rule_id=rule.id,
                    )
                    notifications.append(notification)

                    # Update rule trigger time
                    self._update_rule_trigger_time(rule.id)

        return notifications

    def _should_trigger_rule(self, rule: NotificationRule) -> bool:
        """Check if a rule should be triggered based on frequency."""
        if not rule.is_active:
            return False

        if rule.frequency == "immediate":
            return True

        if not rule.last_triggered:
            return True

        now = datetime.now()
        time_since_last = now - rule.last_triggered

        if rule.frequency == "daily" and time_since_last >= timedelta(days=1):
            return True
        elif rule.frequency == "weekly" and time_since_last >= timedelta(weeks=1):
            return True

        return False

    def _update_rule_trigger_time(self, rule_id: str) -> None:
        """Update the last triggered time for a rule."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE notification_rules SET last_triggered = ? WHERE id = ?
            """,
                (datetime.now().isoformat(), rule_id),
            )

    def get_notifications(self, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        """Get notifications."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM notifications"
            if unread_only:
                query += " WHERE is_read = 0"
            query += " ORDER BY created_date DESC LIMIT ?"

            results = conn.execute(query, (limit,)).fetchall()

            notifications = []
            for result in results:
                notification = Notification(
                    id=result[0],
                    rule_id=result[1],
                    paper_id=result[2],
                    title=result[3],
                    message=result[4],
                    notification_type=NotificationType(result[5]),
                    priority=result[6],
                    is_read=bool(result[7]),
                    created_date=datetime.fromisoformat(result[8]) if result[8] else datetime.now(),
                    data=json.loads(result[9]) if result[9] else {},
                )
                notifications.append(notification)

            return notifications

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE notifications SET is_read = 1 WHERE id = ?
                """,
                    (notification_id,),
                )

            logger.info(f"Marked notification {notification_id} as read")
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    def mark_all_read(self) -> int:
        """Mark all notifications as read."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
            count = cursor.rowcount

        logger.info(f"Marked {count} notifications as read")
        return count

    def get_notification_stats(self) -> NotificationStats:
        """Get notification statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total notifications
            total = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]

            # Unread notifications
            unread = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE is_read = 0"
            ).fetchone()[0]

            # By type
            type_results = conn.execute(
                """
                SELECT notification_type, COUNT(*) FROM notifications
                GROUP BY notification_type
            """
            ).fetchall()
            notifications_by_type = {row[0]: row[1] for row in type_results}

            # By priority
            priority_results = conn.execute(
                """
                SELECT priority, COUNT(*) FROM notifications
                GROUP BY priority
            """
            ).fetchall()
            notifications_by_priority = {row[0]: row[1] for row in priority_results}

            # Active rules
            active_rules = conn.execute(
                "SELECT COUNT(*) FROM notification_rules WHERE is_active = 1"
            ).fetchone()[0]

            # Monitored papers
            monitored_papers = conn.execute(
                "SELECT COUNT(*) FROM paper_monitors WHERE is_active = 1"
            ).fetchone()[0]

            # Last check
            last_check_result = conn.execute(
                "SELECT MAX(last_check) FROM paper_monitors"
            ).fetchone()[0]
            last_check = datetime.fromisoformat(last_check_result) if last_check_result else None

            return NotificationStats(
                total_notifications=total,
                unread_notifications=unread,
                notifications_by_type=notifications_by_type,
                notifications_by_priority=notifications_by_priority,
                active_rules=active_rules,
                monitored_papers=monitored_papers,
                last_check=last_check,
            )

    def register_handler(
        self,
        notification_type: NotificationType,
        handler: Callable[[Notification], None],
    ) -> None:
        """Register a notification handler."""
        self._handlers[notification_type].append(handler)
        logger.info(f"Registered handler for {notification_type.value}")

    def _trigger_handlers(self, notification: Notification) -> None:
        """Trigger registered handlers for a notification."""
        handlers = self._handlers.get(notification.notification_type, [])
        for handler in handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"Handler error for {notification.notification_type.value}: {e}")

    async def run_monitoring_cycle(self) -> int:
        """Run a complete monitoring cycle for all active monitors."""
        notifications_created = 0

        with sqlite3.connect(self.db_path) as conn:
            monitors = conn.execute(
                """
                SELECT paper_id, title, check_frequency, last_check
                FROM paper_monitors
                WHERE is_active = 1
            """
            ).fetchall()

            for monitor in monitors:
                paper_id, title, check_frequency_seconds, last_check_str = monitor
                last_check = (
                    datetime.fromisoformat(last_check_str) if last_check_str else datetime.now()
                )
                check_frequency = timedelta(seconds=check_frequency_seconds)

                # Check if it's time to monitor this paper
                if datetime.now() - last_check >= check_frequency:
                    # In a real implementation, you would fetch current paper data
                    # For now, we'll simulate with mock data
                    current_data = {
                        "arxiv_id": paper_id,
                        "title": title,
                        "version": "1",
                        "authors": [],
                    }

                    notifications = self.check_paper_updates(paper_id, current_data)
                    notifications_created += len(notifications)

        logger.info(f"Monitoring cycle completed: {notifications_created} notifications created")
        return notifications_created

    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Clean up old read notifications."""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM notifications
                WHERE is_read = 1 AND created_date < ?
            """,
                (cutoff_date.isoformat(),),
            )
            count = cursor.rowcount

        logger.info(f"Cleaned up {count} old notifications")
        return count


# Convenience functions
def create_notification_system(
    cache_dir: Optional[str] = None,
) -> PaperNotificationSystem:
    """Create a configured PaperNotificationSystem instance."""
    return PaperNotificationSystem(cache_dir=cache_dir)


def quick_paper_monitor(arxiv_id: str, title: str) -> bool:
    """Quick paper monitoring setup for simple use cases."""
    system = PaperNotificationSystem()
    monitor = system.add_paper_monitor(arxiv_id, title, [])
    return monitor is not None
