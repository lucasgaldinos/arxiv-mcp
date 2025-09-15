"""
Enhanced Multi-Temporal Cleanup API

Provides flexible time specification supporting seconds-to-days precision
while maintaining backward compatibility with existing day-based cleanup systems.
"""

import re
from datetime import datetime, timedelta
from typing import Union, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import logging

logger = logging.getLogger(__name__)


class TimeUnit(Enum):
    """Supported time units for cleanup operations."""

    SECONDS = ("s", "sec", "second", "seconds")
    MINUTES = ("m", "min", "minute", "minutes")
    HOURS = ("h", "hr", "hour", "hours")
    DAYS = ("d", "day", "days")
    WEEKS = ("w", "wk", "week", "weeks")

    def __init__(self, *aliases):
        self.aliases = aliases

    @classmethod
    def from_string(cls, unit_str: str) -> "TimeUnit":
        """Get TimeUnit from string representation."""
        unit_str = unit_str.lower().strip()
        for unit in cls:
            if unit_str in unit.aliases:
                return unit
        raise ValueError(f"Unknown time unit: {unit_str}")


@dataclass
class TimeSpec:
    """Represents a time specification with value and unit."""

    value: int
    unit: TimeUnit

    def to_timedelta(self) -> timedelta:
        """Convert to datetime.timedelta."""
        if self.unit == TimeUnit.SECONDS:
            return timedelta(seconds=self.value)
        elif self.unit == TimeUnit.MINUTES:
            return timedelta(minutes=self.value)
        elif self.unit == TimeUnit.HOURS:
            return timedelta(hours=self.value)
        elif self.unit == TimeUnit.DAYS:
            return timedelta(days=self.value)
        elif self.unit == TimeUnit.WEEKS:
            return timedelta(weeks=self.value)
        else:
            raise ValueError(f"Unsupported time unit: {self.unit}")

    def to_days(self) -> float:
        """Convert to days as float for backward compatibility."""
        delta = self.to_timedelta()
        return delta.total_seconds() / (24 * 3600)

    def __str__(self) -> str:
        return f"{self.value}{self.unit.aliases[0]}"


class MultiTemporalParser:
    """Parser for multi-temporal time specifications."""

    # Regex pattern for parsing time specifications like "2h30m", "1d", "45s"
    TIME_PATTERN = re.compile(
        r"(?:(\d+)\s*([smhdw]|sec|min|hr|hour|day|week|seconds|minutes|hours|days|weeks))",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, time_spec: Union[str, int, float]) -> timedelta:
        """
        Parse time specification into timedelta.

        Args:
            time_spec: Time specification as:
                - String: "30s", "5m", "2h", "1d", "2w", "1h30m", "2d12h30m"
                - Int/Float: Treated as days for backward compatibility

        Returns:
            timedelta object representing the time period

        Examples:
            parse("30s") -> timedelta(seconds=30)
            parse("1h30m") -> timedelta(hours=1, minutes=30)
            parse(7) -> timedelta(days=7)
        """
        if isinstance(time_spec, (int, float)):
            # Backward compatibility: treat numbers as days
            return timedelta(days=time_spec)

        if not isinstance(time_spec, str):
            raise TypeError(f"time_spec must be str, int, or float, got {type(time_spec)}")

        time_spec = time_spec.strip().lower()

        # Find all time components
        matches = cls.TIME_PATTERN.findall(time_spec)

        if not matches:
            raise ValueError(f"Invalid time specification: {time_spec}")

        total_delta = timedelta()

        for value_str, unit_str in matches:
            value = int(value_str)
            unit = TimeUnit.from_string(unit_str)
            spec = TimeSpec(value, unit)
            total_delta += spec.to_timedelta()

        return total_delta

    @classmethod
    def to_human_readable(cls, delta: timedelta) -> str:
        """Convert timedelta to human-readable string."""
        total_seconds = int(delta.total_seconds())

        if total_seconds == 0:
            return "0s"

        components = []

        # Weeks
        weeks = total_seconds // (7 * 24 * 3600)
        if weeks:
            components.append(f"{weeks}w")
            total_seconds %= 7 * 24 * 3600

        # Days
        days = total_seconds // (24 * 3600)
        if days:
            components.append(f"{days}d")
            total_seconds %= 24 * 3600

        # Hours
        hours = total_seconds // 3600
        if hours:
            components.append(f"{hours}h")
            total_seconds %= 3600

        # Minutes
        minutes = total_seconds // 60
        if minutes:
            components.append(f"{minutes}m")
            total_seconds %= 60

        # Seconds
        if total_seconds:
            components.append(f"{total_seconds}s")

        return "".join(components)


class EnhancedCleanupAdapter:
    """
    Adapter layer for enhanced multi-temporal cleanup operations.

    Provides enhanced cleanup capabilities while maintaining compatibility
    with existing day-based cleanup systems.
    """

    def __init__(self, file_saver=None, batch_processor=None, paper_notifications=None):
        """Initialize adapter with optional cleanup providers."""
        self.file_saver = file_saver
        self.batch_processor = batch_processor
        self.paper_notifications = paper_notifications

    def cleanup_files(
        self, time_spec: Union[str, int, float], output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """
        Enhanced file cleanup with multi-temporal support.

        Args:
            time_spec: Time specification (e.g., "2h", "30m", "1d", 7)
            output_dir: Output directory to clean

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Parse time specification
            time_delta = MultiTemporalParser.parse(time_spec)
            cutoff_date = datetime.now() - time_delta

            logger.info(f"Starting cleanup with time spec: {time_spec} (cutoff: {cutoff_date})")

            result = {
                "status": "success",
                "time_spec": str(time_spec),
                "time_spec_parsed": MultiTemporalParser.to_human_readable(time_delta),
                "cutoff_date": cutoff_date.isoformat(),
                "cleaned_files": 0,
                "cleaned_directories": 0,
                "total_size_freed": 0,
                "details": {},
            }

            # Use existing file_saver if available (backward compatibility)
            if self.file_saver:
                # Convert to days for backward compatibility with existing cleanup
                days_old = max(1, int(time_delta.total_seconds() / (24 * 3600)))
                file_cleanup = self.file_saver.cleanup_old_files(days_old)
                result["details"]["file_saver"] = file_cleanup
                result["cleaned_files"] += file_cleanup.get("cleaned_latex", 0) + file_cleanup.get(
                    "cleaned_markdown", 0
                )

            # Enhanced cleanup with precise timing
            if time_delta.total_seconds() < 24 * 3600:  # Sub-day precision
                enhanced_cleanup = self._cleanup_with_precise_timing(cutoff_date, output_dir)
                result["details"]["enhanced"] = enhanced_cleanup
                result["cleaned_files"] += enhanced_cleanup.get("files_cleaned", 0)
                result["cleaned_directories"] += enhanced_cleanup.get("directories_cleaned", 0)
                result["total_size_freed"] += enhanced_cleanup.get("size_freed", 0)

            return result

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"status": "error", "error": str(e), "time_spec": str(time_spec)}

    def _cleanup_with_precise_timing(
        self, cutoff_date: datetime, output_dir: str
    ) -> Dict[str, Any]:
        """Perform cleanup with precise sub-day timing."""
        from pathlib import Path
        import os
        import json

        output_path = Path(output_dir)
        if not output_path.exists():
            return {"files_cleaned": 0, "directories_cleaned": 0, "size_freed": 0}

        files_cleaned = 0
        directories_cleaned = 0
        size_freed = 0

        # Clean files based on modification time
        for root, dirs, files in os.walk(output_path):
            root_path = Path(root)

            # Check files
            for file in files:
                file_path = root_path / file
                try:
                    # Use modification time for sub-day precision
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time < cutoff_date:
                        size_freed += file_path.stat().st_size
                        file_path.unlink()
                        files_cleaned += 1
                        logger.debug(f"Cleaned file: {file_path}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not clean file {file_path}: {e}")

            # Check if directory should be removed (empty after file cleanup)
            if root != str(output_path):  # Don't remove the root output directory
                try:
                    if not any(root_path.iterdir()):  # Directory is empty
                        root_path.rmdir()
                        directories_cleaned += 1
                        logger.debug(f"Cleaned empty directory: {root_path}")
                except (OSError, PermissionError):
                    pass  # Directory not empty or permission issue

        return {
            "files_cleaned": files_cleaned,
            "directories_cleaned": directories_cleaned,
            "size_freed": size_freed,
        }

    def cleanup_batch_operations(self, time_spec: Union[str, int, float]) -> Dict[str, Any]:
        """Clean up batch operations with multi-temporal support."""
        if not self.batch_processor:
            return {"status": "skipped", "reason": "No batch processor component available"}

        try:
            time_delta = MultiTemporalParser.parse(time_spec)
            # Convert to days for existing API, but provide enhanced logging
            days = max(1, int(time_delta.total_seconds() / (24 * 3600)))

            cleaned_count = self.batch_processor.cleanup_completed_operations(days)

            return {
                "status": "success",
                "time_spec": str(time_spec),
                "time_spec_parsed": MultiTemporalParser.to_human_readable(time_delta),
                "cleaned_operations": cleaned_count,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def cleanup_notifications(self, time_spec: Union[str, int, float]) -> Dict[str, Any]:
        """Clean up notifications with multi-temporal support."""
        if not self.paper_notifications:
            return {"status": "skipped", "reason": "No notifications component available"}

        try:
            time_delta = MultiTemporalParser.parse(time_spec)
            # Convert to days for existing API
            days = max(1, int(time_delta.total_seconds() / (24 * 3600)))

            cleaned_count = self.paper_notifications.cleanup_old_notifications(days)

            return {
                "status": "success",
                "time_spec": str(time_spec),
                "time_spec_parsed": MultiTemporalParser.to_human_readable(time_delta),
                "cleaned_notifications": cleaned_count,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def comprehensive_cleanup(
        self, time_spec: Union[str, int, float], output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive cleanup across all systems.

        Args:
            time_spec: Time specification for cleanup threshold
            output_dir: Output directory to clean

        Returns:
            Comprehensive cleanup results
        """
        try:
            time_delta = MultiTemporalParser.parse(time_spec)

            result = {
                "status": "success",
                "time_spec": str(time_spec),
                "time_spec_parsed": MultiTemporalParser.to_human_readable(time_delta),
                "started_at": datetime.now().isoformat(),
                "components": {},
            }

            # Clean files
            file_result = self.cleanup_files(time_spec, output_dir)
            result["components"]["files"] = file_result

            # Clean batch operations
            batch_result = self.cleanup_batch_operations(time_spec)
            result["components"]["batch_operations"] = batch_result

            # Clean notifications
            notifications_result = self.cleanup_notifications(time_spec)
            result["components"]["notifications"] = notifications_result

            # Summary statistics
            result["summary"] = {
                "total_files_cleaned": file_result.get("cleaned_files", 0),
                "total_directories_cleaned": file_result.get("cleaned_directories", 0),
                "total_size_freed": file_result.get("total_size_freed", 0),
                "operations_cleaned": batch_result.get("cleaned_operations", 0),
                "notifications_cleaned": notifications_result.get("cleaned_notifications", 0),
            }

            result["completed_at"] = datetime.now().isoformat()

            logger.info(f"Comprehensive cleanup completed: {result['summary']}")

            return result

        except Exception as e:
            logger.error(f"Comprehensive cleanup failed: {e}")
            return {"status": "error", "error": str(e), "time_spec": str(time_spec)}


# Backward compatibility functions
def create_enhanced_adapter(config=None) -> EnhancedCleanupAdapter:
    """
    Factory function to create enhanced cleanup adapter with proper dependencies.

    Args:
        config: Optional pipeline configuration

    Returns:
        Configured EnhancedCleanupAdapter instance
    """
    from ..utils.file_saver import FileSaver
    from ..utils.batch_operations import BatchProcessor
    from ..utils.paper_notifications import PaperNotificationSystem

    try:
        # Initialize components
        file_saver = None
        batch_processor = None
        paper_notifications = None

        if config:
            try:
                file_saver = FileSaver(output_dir=getattr(config, "output_directory", "./output"))
            except Exception as e:
                logger.warning(f"Could not initialize FileSaver: {e}")

            try:
                batch_processor = BatchProcessor()
            except Exception as e:
                logger.warning(f"Could not initialize BatchProcessor: {e}")

            try:
                paper_notifications = PaperNotificationSystem()
            except Exception as e:
                logger.warning(f"Could not initialize PaperNotificationSystem: {e}")

        return EnhancedCleanupAdapter(
            file_saver=file_saver,
            batch_processor=batch_processor,
            paper_notifications=paper_notifications,
        )

    except Exception as e:
        logger.error(f"Failed to create enhanced adapter: {e}")
        # Return minimal adapter for graceful degradation
        return EnhancedCleanupAdapter()
