#!/usr/bin/env python3
"""
Integration tests for batch_operations.py with real coverage measurement.

Uses minimal mocking approach to enable proper coverage tracking across
ThreadPoolExecutor boundaries. Based on proven pattern from unified_converter tests.
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
from typing import Any, Dict, Generator

from arxiv_mcp.utils.batch_operations import (
    BatchProcessor,
    BatchOperationType,
    BatchStatus
)


@pytest.fixture
def temp_cache_dir() -> Generator[str, None, None]:
    """Create temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def batch_processor(temp_cache_dir: str) -> Generator[BatchProcessor, None, None]:
    """Create BatchProcessor instance for testing."""
    processor = BatchProcessor(max_workers=2, cache_dir=temp_cache_dir)
    yield processor
    processor.shutdown()


def sample_handler(input_data: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Sample handler function for testing batch operations."""
    config = config or {}
    text = input_data.get("text", "")
    operation = input_data.get("operation", "uppercase")
    
    if operation == "uppercase":
        result = text.upper()
    elif operation == "lowercase":
        result = text.lower()
    elif operation == "length":
        result = len(text)
    elif operation == "reverse":
        result = text[::-1]
    else:
        result = text
    
    return {"result": result, "original": text}


def error_handler(input_data: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Handler that raises an error for testing error handling."""
    raise ValueError("Simulated error")


class TestBatchProcessorIntegration:
    """Integration tests for BatchProcessor with real code execution."""

    def test_constructor_and_basic_setup(self, temp_cache_dir: str) -> None:
        """Test BatchProcessor initialization and basic setup."""
        processor = BatchProcessor(max_workers=3, cache_dir=temp_cache_dir)
        
        # Verify initialization
        assert processor.max_workers == 3
        assert processor.cache_dir == Path(temp_cache_dir)
        assert processor.cache_dir.exists()
        assert len(processor.operations) == 0
        # Note: handlers dict type is dynamic, so we skip specific type checks
        
        processor.shutdown()

    def test_handler_registration(self, batch_processor: BatchProcessor) -> None:
        """Test registering operation handlers."""
        # Register a handler
        batch_processor.register_handler(BatchOperationType.TRANSFORM, sample_handler)
        
        # Verify handler is registered
        assert BatchOperationType.TRANSFORM in batch_processor.handlers
        assert batch_processor.handlers[BatchOperationType.TRANSFORM] == sample_handler

    @pytest.mark.asyncio
    async def test_basic_batch_operation(self, batch_processor: BatchProcessor) -> None:
        """Test basic batch operation execution."""
        # Register handler
        batch_processor.register_handler(BatchOperationType.TRANSFORM, sample_handler)
        
        # Create test data
        items_data = [
            {"text": "hello", "operation": "uppercase"},
            {"text": "WORLD", "operation": "lowercase"},
            {"text": "test", "operation": "length"}
        ]
        
        # Create and execute batch operation
        operation = batch_processor.create_batch_operation(
            BatchOperationType.TRANSFORM,
            items_data
        )
        
        # Execute the batch
        batch_processor.submit_batch_operation(operation.id)
        
        # Wait for completion with timeout
        timeout = 10  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while operation.status not in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]:
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            await asyncio.sleep(0.1)
        
        # Verify results
        assert operation.status in [BatchStatus.COMPLETED, BatchStatus.PARTIAL]
        assert operation.completed_items >= 2  # At least some items completed
        
        # Check individual item results
        completed_items = [item for item in operation.items if item.status == BatchStatus.COMPLETED]
        assert len(completed_items) >= 2
        
        # Verify specific transformations
        for item in completed_items:
            assert item.output_data is not None
            assert "result" in item.output_data
            assert "original" in item.output_data

    @pytest.mark.asyncio
    async def test_batch_operation_with_config(self, batch_processor: BatchProcessor) -> None:
        """Test batch operation with configuration options."""
        # Register handler
        batch_processor.register_handler(BatchOperationType.ANALYZE, sample_handler)
        
        # Create test data with config
        items_data = [
            {"text": "test1", "operation": "reverse"},
            {"text": "test2", "operation": "reverse"}
        ]
        
        config = {
            "delay": 0.1,  # Small delay for testing
            "max_concurrent": 1
        }
        
        # Create and execute batch operation
        operation = batch_processor.create_batch_operation(
            BatchOperationType.ANALYZE,
            items_data,
            config
        )
        
        batch_processor.submit_batch_operation(operation.id)
        
        # Wait for completion
        timeout = 15  # Longer timeout due to delays
        start_time = asyncio.get_event_loop().time()
        
        while operation.status not in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]:
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            await asyncio.sleep(0.1)
        
        # Verify results
        assert operation.status in [BatchStatus.COMPLETED, BatchStatus.PARTIAL]
        
        # Check that results are reversed strings
        completed_items = [item for item in operation.items if item.status == BatchStatus.COMPLETED]
        for item in completed_items:
            assert item.output_data is not None
            original = item.output_data["original"]
            result = item.output_data["result"]
            assert result == original[::-1]

    @pytest.mark.asyncio
    async def test_error_handling_in_batch(self, batch_processor: BatchProcessor) -> None:
        """Test error handling during batch processing."""
        # Register both good and error handlers
        batch_processor.register_handler(BatchOperationType.TRANSFORM, sample_handler)
        batch_processor.register_handler(BatchOperationType.VALIDATE, error_handler)
        
        # Create operation that will have errors
        items_data = [
            {"text": "will_fail"}
        ]
        
        operation = batch_processor.create_batch_operation(
            BatchOperationType.VALIDATE,
            items_data
        )
        
        batch_processor.submit_batch_operation(operation.id)
        
        # Wait for completion
        timeout = 10
        start_time = asyncio.get_event_loop().time()
        
        while operation.status not in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]:
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            await asyncio.sleep(0.1)
        
        # Verify error handling
        assert operation.status in [BatchStatus.FAILED, BatchStatus.PARTIAL]
        assert operation.failed_items > 0
        
        failed_items = [item for item in operation.items if item.status == BatchStatus.FAILED]
        assert len(failed_items) > 0
        assert any("Simulated error" in (item.error_message or "") for item in failed_items)

    def test_operation_persistence(self, batch_processor: BatchProcessor) -> None:
        """Test that operations are persisted and can be retrieved."""
        # Create operation
        items_data = [{"text": "persistence_test"}]
        
        operation = batch_processor.create_batch_operation(
            BatchOperationType.EXPORT,
            items_data
        )
        
        # Verify operation is stored
        assert operation.id in batch_processor.operations
        retrieved_operation = batch_processor.get_batch_operation(operation.id)
        assert retrieved_operation is not None
        assert retrieved_operation == operation
        assert retrieved_operation.total_items == 1

    def test_shutdown_cleanup(self, temp_cache_dir: str) -> None:
        """Test proper cleanup during shutdown."""
        processor = BatchProcessor(max_workers=2, cache_dir=temp_cache_dir)
        
        # Verify executor is running
        assert processor.executor is not None
        assert not processor.executor._shutdown
        
        # Shutdown and verify cleanup
        processor.shutdown()
        assert processor.executor._shutdown