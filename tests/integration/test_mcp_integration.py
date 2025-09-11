"""
Integration test for the new process_document_formats MCP tool.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arxiv_mcp.tools import handle_process_document_formats


def test_supported_formats():
    """Test getting supported formats."""
    result = handle_process_document_formats(supported_formats=True)

    assert result["status"] == "success"
    assert "supported_formats" in result
    assert "pdf" in result["supported_formats"]
    assert "odt" in result["supported_formats"]
    assert "rtf" in result["supported_formats"]
    assert "docx" in result["supported_formats"]
    assert "txt" in result["supported_formats"]

    # Check format details
    assert "format_details" in result
    assert "pdf" in result["format_details"]
    assert "extensions" in result["format_details"]["pdf"]


def test_text_processing():
    """Test processing a simple text file."""
    import tempfile
    import os

    # Create a temporary text file
    test_content = b"This is a test document for the new MCP tool.\n\nIt has multiple paragraphs and should be processed correctly."

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(test_content)
        tmp_path = tmp.name

    try:
        result = handle_process_document_formats(
            file_path=tmp_path, extract_metadata=True
        )

        assert result["status"] == "success"
        assert result["format"] == "txt"
        assert "test document" in result["extracted_text"]
        assert "metadata" in result
        assert result["metadata"]["format"] == "txt"
        assert result["metadata"]["word_count"] > 0

    finally:
        os.unlink(tmp_path)


def test_error_handling():
    """Test error handling for invalid input."""
    # Test missing both file_path and document_content
    result = handle_process_document_formats()
    assert result["status"] == "error"
    assert "Either file_path or document_content must be provided" in result["error"]

    # Test document_content without filename
    result = handle_process_document_formats(
        document_content="dGVzdA=="
    )  # "test" in base64
    assert result["status"] == "error"
    assert "filename is required" in result["error"]


if __name__ == "__main__":
    test_supported_formats()
    test_text_processing()
    test_error_handling()
    print("✅ All integration tests passed!")
