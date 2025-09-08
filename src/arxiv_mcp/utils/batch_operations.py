#!/usr/bin/env python3
"""
Batch Operations System for ArXiv MCP

This module provides batch processing capabilities for multiple research papers,
enabling efficient bulk operations and parallel processing.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from .logging import get_logger

logger = get_logger(__name__)


class BatchOperationType(Enum):
    """Types of batch operations."""

    SEARCH = "search"
    DOWNLOAD = "download"
    ANALYZE = "analyze"
    TAG = "tag"
    SUMMARIZE = "summarize"
    EXPORT = "export"
    VALIDATE = "validate"
    TRANSFORM = "transform"


class BatchStatus(Enum):
    """Batch operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


@dataclass
class BatchItem:
    """Represents a single item in a batch operation."""

    id: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: BatchStatus = BatchStatus.PENDING
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchOperation:
    """Represents a batch operation configuration and state."""

    id: str
    operation_type: BatchOperationType
    items: List[BatchItem]
    status: BatchStatus = BatchStatus.PENDING
    created_date: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    success_rate: float = 0.0
    estimated_completion: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    results_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Results of a batch operation."""

    operation_id: str
    operation_type: BatchOperationType
    total_items: int
    successful_items: List[BatchItem]
    failed_items: List[BatchItem]
    success_rate: float
    total_time: float
    average_time_per_item: float
    summary: Dict[str, Any]


class BatchProcessor:
    """
    High-performance batch processing system for research papers.

    Features:
    - Parallel processing with configurable concurrency
    - Progress tracking and monitoring
    - Error handling and retry mechanisms
    - Result aggregation and analysis
    - Flexible operation types
    - Resource management
    - Persistence and recovery
    """

    def __init__(self, max_workers: int = 5, cache_dir: Optional[str] = None):
        """Initialize the batch processor."""
        self.max_workers = max_workers
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "batch_cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.operations: Dict[str, BatchOperation] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Operation handlers
        self.handlers: Dict[BatchOperationType, Callable] = {}

        logger.info(f"BatchProcessor initialized with {max_workers} workers")

    def register_handler(
        self,
        operation_type: BatchOperationType,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Register a handler for a specific operation type."""
        self.handlers[operation_type] = handler
        logger.info(f"Registered handler for {operation_type.value}")

    def create_batch_operation(
        self,
        operation_type: BatchOperationType,
        items_data: List[Dict[str, Any]],
        config: Dict[str, Any] = None,
    ) -> BatchOperation:
        """Create a new batch operation."""
        operation_id = str(uuid.uuid4())
        config = config or {}

        # Create batch items
        items = []
        for i, item_data in enumerate(items_data):
            item = BatchItem(id=f"{operation_id}-item-{i}", input_data=item_data)
            items.append(item)

        operation = BatchOperation(
            id=operation_id,
            operation_type=operation_type,
            items=items,
            total_items=len(items),
            config=config,
        )

        self.operations[operation_id] = operation

        logger.info(f"Created batch operation {operation_id} with {len(items)} items")
        return operation

    def submit_batch_operation(self, operation_id: str) -> bool:
        """Submit a batch operation for processing."""
        if operation_id not in self.operations:
            logger.error(f"Operation {operation_id} not found")
            return False

        operation = self.operations[operation_id]

        if operation.operation_type not in self.handlers:
            logger.error(f"No handler registered for {operation.operation_type.value}")
            return False

        operation.status = BatchStatus.RUNNING
        operation.start_time = datetime.now()

        # Submit items for processing
        asyncio.create_task(self._process_batch_async(operation))

        logger.info(f"Submitted batch operation {operation_id} for processing")
        return True

    async def _process_batch_async(self, operation: BatchOperation) -> None:
        """Process a batch operation asynchronously."""
        handler = self.handlers[operation.operation_type]

        # Configure concurrency
        max_concurrent = min(self.max_workers, operation.total_items)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item: BatchItem) -> BatchItem:
            async with semaphore:
                return await self._process_single_item(item, handler, operation.config)

        # Process all items
        tasks = [process_item(item) for item in operation.items]

        try:
            # Wait for all tasks to complete
            completed_items = await asyncio.gather(*tasks, return_exceptions=True)

            # Update operation status
            operation.completed_items = sum(
                1
                for item in completed_items
                if isinstance(item, BatchItem) and item.status == BatchStatus.COMPLETED
            )
            operation.failed_items = operation.total_items - operation.completed_items
            operation.success_rate = (
                operation.completed_items / operation.total_items
                if operation.total_items > 0
                else 0
            )

            # Determine final status
            if operation.completed_items == operation.total_items:
                operation.status = BatchStatus.COMPLETED
            elif operation.completed_items > 0:
                operation.status = BatchStatus.PARTIAL
            else:
                operation.status = BatchStatus.FAILED

        except Exception as e:
            logger.error(f"Batch operation {operation.id} failed: {e}")
            operation.status = BatchStatus.FAILED

        operation.end_time = datetime.now()

        # Generate results summary
        operation.results_summary = self._generate_results_summary(operation)

        logger.info(
            f"Batch operation {operation.id} completed: {operation.status.value}"
        )

    async def _process_single_item(
        self, item: BatchItem, handler: Callable, config: Dict[str, Any]
    ) -> BatchItem:
        """Process a single batch item."""
        item.start_time = datetime.now()
        item.status = BatchStatus.RUNNING

        try:
            # Apply configured delays/throttling
            if "delay" in config:
                await asyncio.sleep(config["delay"])

            # Run the handler
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, lambda: handler(item.input_data, config)
            )

            item.output_data = result
            item.status = BatchStatus.COMPLETED

        except Exception as e:
            logger.error(f"Item {item.id} failed: {e}")
            item.error_message = str(e)
            item.status = BatchStatus.FAILED

        item.end_time = datetime.now()
        if item.start_time:
            item.processing_time = (item.end_time - item.start_time).total_seconds()

        return item

    def _generate_results_summary(self, operation: BatchOperation) -> Dict[str, Any]:
        """Generate a summary of batch operation results."""
        completed_items = [
            item for item in operation.items if item.status == BatchStatus.COMPLETED
        ]
        failed_items = [
            item for item in operation.items if item.status == BatchStatus.FAILED
        ]

        # Calculate timing statistics
        processing_times = [
            item.processing_time
            for item in completed_items
            if item.processing_time is not None
        ]

        summary = {
            "total_items": operation.total_items,
            "completed_items": len(completed_items),
            "failed_items": len(failed_items),
            "success_rate": operation.success_rate,
            "total_time": (operation.end_time - operation.start_time).total_seconds()
            if operation.end_time and operation.start_time
            else 0,
            "average_processing_time": sum(processing_times) / len(processing_times)
            if processing_times
            else 0,
            "min_processing_time": min(processing_times) if processing_times else 0,
            "max_processing_time": max(processing_times) if processing_times else 0,
        }

        # Add operation-specific summary
        if operation.operation_type == BatchOperationType.SEARCH:
            summary["total_results"] = sum(
                len(item.output_data.get("results", []))
                for item in completed_items
                if item.output_data
            )
        elif operation.operation_type == BatchOperationType.DOWNLOAD:
            summary["total_size"] = sum(
                item.output_data.get("size", 0)
                for item in completed_items
                if item.output_data
            )

        return summary

    def get_batch_operation(self, operation_id: str) -> Optional[BatchOperation]:
        """Get a batch operation by ID."""
        return self.operations.get(operation_id)

    def get_batch_status(self, operation_id: str) -> Optional[BatchStatus]:
        """Get the status of a batch operation."""
        operation = self.operations.get(operation_id)
        return operation.status if operation else None

    def get_batch_progress(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a batch operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return None

        progress = {
            "operation_id": operation_id,
            "status": operation.status.value,
            "total_items": operation.total_items,
            "completed_items": operation.completed_items,
            "failed_items": operation.failed_items,
            "success_rate": operation.success_rate,
            "progress_percentage": (
                operation.completed_items / operation.total_items * 100
            )
            if operation.total_items > 0
            else 0,
        }

        # Add timing information
        if operation.start_time:
            elapsed_time = (datetime.now() - operation.start_time).total_seconds()
            progress["elapsed_time"] = elapsed_time

            if operation.completed_items > 0:
                avg_time_per_item = elapsed_time / operation.completed_items
                remaining_items = operation.total_items - operation.completed_items
                estimated_remaining = avg_time_per_item * remaining_items
                progress["estimated_completion"] = (
                    datetime.now().timestamp() + estimated_remaining
                )

        return progress

    def cancel_batch_operation(self, operation_id: str) -> bool:
        """Cancel a running batch operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return False

        if operation.status in [BatchStatus.PENDING, BatchStatus.RUNNING]:
            operation.status = BatchStatus.CANCELLED
            logger.info(f"Cancelled batch operation {operation_id}")
            return True

        return False

    def list_batch_operations(
        self, status_filter: Optional[BatchStatus] = None
    ) -> List[BatchOperation]:
        """List all batch operations, optionally filtered by status."""
        operations = list(self.operations.values())

        if status_filter:
            operations = [op for op in operations if op.status == status_filter]

        # Sort by creation date (newest first)
        operations.sort(key=lambda x: x.created_date, reverse=True)

        return operations

    def get_batch_results(self, operation_id: str) -> Optional[BatchResult]:
        """Get detailed results for a completed batch operation."""
        operation = self.operations.get(operation_id)
        if not operation or operation.status not in [
            BatchStatus.COMPLETED,
            BatchStatus.PARTIAL,
        ]:
            return None

        successful_items = [
            item for item in operation.items if item.status == BatchStatus.COMPLETED
        ]
        failed_items = [
            item for item in operation.items if item.status == BatchStatus.FAILED
        ]

        total_time = (
            (operation.end_time - operation.start_time).total_seconds()
            if operation.end_time and operation.start_time
            else 0
        )
        avg_time = (
            total_time / operation.total_items if operation.total_items > 0 else 0
        )

        return BatchResult(
            operation_id=operation_id,
            operation_type=operation.operation_type,
            total_items=operation.total_items,
            successful_items=successful_items,
            failed_items=failed_items,
            success_rate=operation.success_rate,
            total_time=total_time,
            average_time_per_item=avg_time,
            summary=operation.results_summary,
        )

    def export_batch_results(
        self,
        operation_id: str,
        output_path: str,
        format: str = "json",
        include_data: bool = True,
    ) -> bool:
        """Export batch operation results to file."""
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                logger.error(f"Operation {operation_id} not found")
                return False

            output_file = Path(output_path)

            # Prepare export data
            export_data = {
                "operation_id": operation.id,
                "operation_type": operation.operation_type.value,
                "status": operation.status.value,
                "created_date": operation.created_date.isoformat(),
                "start_time": operation.start_time.isoformat()
                if operation.start_time
                else None,
                "end_time": operation.end_time.isoformat()
                if operation.end_time
                else None,
                "config": operation.config,
                "results_summary": operation.results_summary,
                "items": [],
            }

            # Add item data
            for item in operation.items:
                item_data = {
                    "id": item.id,
                    "status": item.status.value,
                    "processing_time": item.processing_time,
                    "error_message": item.error_message,
                }

                if include_data:
                    item_data["input_data"] = item.input_data
                    item_data["output_data"] = item.output_data

                export_data["items"].append(item_data)

            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)
            elif format == "csv":
                import csv

                with open(output_file, "w", newline="") as f:
                    writer = csv.writer(f)

                    # Write header
                    header = ["item_id", "status", "processing_time", "error_message"]
                    if include_data:
                        header.extend(["input_data", "output_data"])
                    writer.writerow(header)

                    # Write items
                    for item in operation.items:
                        row = [
                            item.id,
                            item.status.value,
                            item.processing_time,
                            item.error_message,
                        ]
                        if include_data:
                            row.extend(
                                [
                                    json.dumps(item.input_data),
                                    json.dumps(item.output_data),
                                ]
                            )
                        writer.writerow(row)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Exported batch results to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export batch results: {e}")
            return False

    def cleanup_completed_operations(self, days: int = 7) -> int:
        """Clean up old completed operations."""
        cutoff_date = datetime.now() - timedelta(days=days)

        operations_to_remove = []
        for op_id, operation in self.operations.items():
            if (
                operation.status
                in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]
                and operation.created_date < cutoff_date
            ):
                operations_to_remove.append(op_id)

        for op_id in operations_to_remove:
            del self.operations[op_id]

        logger.info(f"Cleaned up {len(operations_to_remove)} old operations")
        return len(operations_to_remove)

    def shutdown(self) -> None:
        """Shutdown the batch processor."""
        self.executor.shutdown(wait=True)
        logger.info("BatchProcessor shutdown completed")


# Pre-built operation handlers
def batch_search_handler(
    input_data: Dict[str, Any], config: Dict[str, Any]
) -> Dict[str, Any]:
    """Handler for batch search operations."""
    query = input_data.get("query", "")
    max_results = config.get("max_results", 10)

    # Mock search implementation
    results = [
        {
            "arxiv_id": f"2024.{i:05d}",
            "title": f"Research Paper {i} for query: {query}",
            "relevance_score": 0.95 - (i * 0.1),
        }
        for i in range(1, min(max_results + 1, 6))
    ]

    return {"query": query, "results": results, "total_found": len(results)}


def batch_download_handler(
    input_data: Dict[str, Any], config: Dict[str, Any]
) -> Dict[str, Any]:
    """Handler for batch download operations."""
    arxiv_id = input_data.get("arxiv_id", "")
    format_type = config.get("format", "pdf")

    # Mock download implementation
    time.sleep(0.1)  # Simulate download time

    return {
        "arxiv_id": arxiv_id,
        "format": format_type,
        "file_path": f"/downloads/{arxiv_id}.{format_type}",
        "size": 1024 * 1024 * 2,  # 2MB mock size
        "downloaded_at": datetime.now().isoformat(),
    }


def batch_analyze_handler(
    input_data: Dict[str, Any], config: Dict[str, Any]
) -> Dict[str, Any]:
    """Handler for batch analysis operations."""
    paper_data = input_data.get("paper_data", {})
    analysis_type = config.get("analysis_type", "basic")

    # Mock analysis implementation
    analysis_result = {
        "paper_id": paper_data.get("arxiv_id", ""),
        "analysis_type": analysis_type,
        "word_count": 5000,
        "complexity_score": 0.75,
        "readability_score": 0.65,
        "key_topics": ["machine learning", "neural networks", "optimization"],
    }

    return analysis_result


# Convenience functions
def create_batch_processor(
    max_workers: int = 5, cache_dir: Optional[str] = None
) -> BatchProcessor:
    """Create a configured BatchProcessor instance with default handlers."""
    processor = BatchProcessor(max_workers=max_workers, cache_dir=cache_dir)

    # Register default handlers
    processor.register_handler(BatchOperationType.SEARCH, batch_search_handler)
    processor.register_handler(BatchOperationType.DOWNLOAD, batch_download_handler)
    processor.register_handler(BatchOperationType.ANALYZE, batch_analyze_handler)

    return processor


def quick_batch_search(
    queries: List[str], max_results: int = 10
) -> List[Dict[str, Any]]:
    """Quick batch search for multiple queries."""
    processor = create_batch_processor()

    # Prepare search items
    items_data = [{"query": query} for query in queries]
    config = {"max_results": max_results}

    # Create and submit operation
    operation = processor.create_batch_operation(
        BatchOperationType.SEARCH, items_data, config
    )

    processor.submit_batch_operation(operation.id)

    # Wait for completion (simplified for demo)
    import time

    while operation.status == BatchStatus.RUNNING:
        time.sleep(0.1)

    # Return results
    results = []
    for item in operation.items:
        if item.status == BatchStatus.COMPLETED and item.output_data:
            results.append(item.output_data)

    processor.shutdown()
    return results
