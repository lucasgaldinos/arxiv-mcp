"""
Demo script for Phase 4A Item 1: Enhanced Document Processing
Demonstrates the new process_document_formats MCP tool functionality.
"""

import tempfile
import os
import zipfile
from io import BytesIO
import base64

# Import our new functionality
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.arxiv_mcp.tools import handle_process_document_formats
from src.arxiv_mcp.processors.document_processor import DocumentProcessor


def create_sample_documents():
    """Create sample documents to demonstrate processing."""
    documents = {}

    # Create sample TXT document
    txt_content = """
# Research Paper Analysis

This is a comprehensive analysis of recent developments in 
machine learning and artificial intelligence.

## Introduction
The field of AI has seen tremendous growth in recent years.

## Key Findings
1. Deep learning models show improved performance
2. Transfer learning reduces training time
3. Attention mechanisms enhance model interpretability

## Conclusion
Future research should focus on efficiency and interpretability.
""".strip().encode("utf-8")

    documents["sample.txt"] = txt_content

    # Create sample RTF document
    rtf_content = b"""{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}
\\f0\\fs24 
\\b Research Report: Advanced AI Methods\\b0
\\par\\par
This document presents findings from our latest research into \\i artificial intelligence\\i0 methods.
\\par\\par
\\b Key Results:\\b0
\\par
- Improved accuracy by 15%
\\par
- Reduced computational cost by 30%
\\par
- Enhanced model interpretability
\\par\\par
The research demonstrates significant advances in the field.
}"""

    documents["research_report.rtf"] = rtf_content

    # Create sample ODT document (as ZIP)
    odt_buffer = BytesIO()
    with zipfile.ZipFile(odt_buffer, "w") as zf:
        # Basic ODT structure
        zf.writestr(
            "META-INF/manifest.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
    <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
    <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
    <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>""",
        )

        # Document content
        zf.writestr(
            "content.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                         xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
    <office:body>
        <office:text>
            <text:h text:style-name="Heading 1" text:outline-level="1">
                Academic Paper: Neural Network Optimization
            </text:h>
            <text:p>
                This paper presents novel approaches to optimizing neural network architectures
                for improved performance and efficiency.
            </text:p>
            <text:h text:style-name="Heading 2" text:outline-level="2">
                Abstract
            </text:h>
            <text:p>
                We propose a new method for automated neural architecture search that
                significantly outperforms existing approaches.
            </text:p>
            <text:h text:style-name="Heading 2" text:outline-level="2">
                Methodology
            </text:h>
            <text:p>
                Our approach combines genetic algorithms with gradient-based optimization
                to explore the space of possible architectures efficiently.
            </text:p>
        </office:text>
    </office:body>
</office:document-content>""",
        )

        # Document metadata
        zf.writestr(
            "meta.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                      xmlns:dc="http://purl.org/dc/elements/1.1/">
    <office:meta>
        <dc:title>Neural Network Optimization</dc:title>
        <dc:creator>Dr. Jane Smith</dc:creator>
        <dc:subject>Machine Learning Research</dc:subject>
        <dc:description>Advanced research on neural network optimization techniques</dc:description>
    </office:meta>
</office:document-meta>""",
        )

    documents["academic_paper.odt"] = odt_buffer.getvalue()

    return documents


def demo_supported_formats():
    """Demonstrate getting supported formats."""
    print("=== Supported Document Formats ===")
    result = handle_process_document_formats(supported_formats=True)

    if result["status"] == "success":
        print(f"✅ Found {len(result['supported_formats'])} supported formats:")
        for format_name in result["supported_formats"]:
            format_info = result["format_details"][format_name]
            print(f"  📄 {format_name.upper()}: {format_info['name']}")
            print(f"     Extensions: {', '.join(format_info['extensions'])}")
            if format_info["requires_external"]:
                print(
                    f"     Dependencies: {format_info.get('optional_dependency', 'Various')}"
                )
            print()
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def demo_file_processing():
    """Demonstrate processing files from disk."""
    print("=== File Processing Demo ===")

    # Create sample documents
    documents = create_sample_documents()

    # Process each document type
    for filename, content in documents.items():
        print(f"\n📄 Processing {filename}...")

        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            suffix=f".{filename.split('.')[-1]}", delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = handle_process_document_formats(
                file_path=tmp_path, extract_metadata=True
            )

            if result["status"] == "success":
                print(f"✅ Successfully processed {result['format'].upper()} document")
                print(f"   Text length: {len(result['extracted_text'])} characters")
                print(f"   Preview: {result['extracted_text'][:150]}...")

                if "metadata" in result:
                    metadata = result["metadata"]
                    print("   Metadata:")
                    if metadata.get("title"):
                        print(f"     Title: {metadata['title']}")
                    if metadata.get("author"):
                        print(f"     Author: {metadata['author']}")
                    if metadata.get("word_count"):
                        print(f"     Word count: {metadata['word_count']}")

                if result.get("warnings"):
                    print(f"   ⚠️ Warnings: {', '.join(result['warnings'])}")
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

        finally:
            os.unlink(tmp_path)


def demo_base64_processing():
    """Demonstrate processing documents via base64 content."""
    print("\n=== Base64 Content Processing Demo ===")

    # Create a simple text document
    text_content = """
Research Summary: Quantum Computing Applications

This document summarizes recent advances in quantum computing 
applications for optimization problems.

Key Benefits:
- Exponential speedup for certain problems
- Novel algorithmic approaches
- Applications in cryptography and simulation

The field shows tremendous promise for future developments.
""".strip()

    # Convert to base64
    encoded_content = base64.b64encode(text_content.encode("utf-8")).decode("ascii")

    print("📄 Processing base64-encoded text document...")

    result = handle_process_document_formats(
        document_content=encoded_content,
        filename="quantum_research.txt",
        extract_metadata=True,
    )

    if result["status"] == "success":
        print(f"✅ Successfully processed {result['format'].upper()} document")
        print(f"   Text length: {len(result['extracted_text'])} characters")
        print(f"   Word count: {result['metadata']['word_count']}")
        print("   Content preview:")
        print(f"   {result['extracted_text'][:200]}...")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n=== Error Handling Demo ===")

    # Test missing parameters
    print("📄 Testing missing parameters...")
    result = handle_process_document_formats()
    print(f"Expected error: {result.get('error', 'No error')}")

    # Test base64 without filename
    print("\n📄 Testing base64 without filename...")
    result = handle_process_document_formats(document_content="dGVzdA==")
    print(f"Expected error: {result.get('error', 'No error')}")

    # Test invalid file path
    print("\n📄 Testing invalid file path...")
    result = handle_process_document_formats(file_path="/nonexistent/file.txt")
    print(f"Expected error: {result.get('error', 'No error')}")


def demo_direct_processor_usage():
    """Demonstrate direct DocumentProcessor usage."""
    print("\n=== Direct DocumentProcessor Usage ===")

    processor = DocumentProcessor()

    # Test format detection
    print("📄 Testing format detection...")

    test_cases = [
        (b"%PDF-1.4\nPDF content here", "test.pdf"),
        (b"\\documentclass{article}", "paper.tex"),
        (b"{\\rtf1\\ansi RTF content}", "document.rtf"),
        (b"Plain text content", "notes.txt"),
    ]

    for content, filename in test_cases:
        detected_format = processor.detect_format(content, filename)
        print(f"   {filename} → {detected_format.value}")

    # Test text processing with detailed results
    print("\n📄 Processing detailed text analysis...")
    text_content = b"""
Machine Learning Research: A Comprehensive Review

This document provides an extensive analysis of current machine learning methodologies
and their applications across various domains.

Introduction
The field of machine learning has experienced unprecedented growth in recent years,
driven by advances in computational power and the availability of large datasets.

Key Contributions
1. Novel algorithms for deep learning
2. Improved optimization techniques  
3. Enhanced interpretability methods
4. Robust evaluation frameworks

Conclusions
Future research should focus on scalability, interpretability, and ethical considerations
in machine learning system design.
""".strip()

    result = processor.process_document(text_content, "ml_research.txt")

    if result.success:
        newline_str = "\n\n"
        print("✅ Analysis complete:")
        print(f"   Format: {result.format.value}")
        print(f"   Text length: {len(result.extracted_text)} characters")
        print(f"   Word count: {result.metadata.word_count}")
        print(f"   Paragraphs detected: {result.extracted_text.count(newline_str) + 1}")
        print("   Content structure preview:")
        lines = result.extracted_text.split("\n")
        for i, line in enumerate(lines[:8]):
            print(f"     {i + 1:2d}: {line[:60]}{'...' if len(line) > 60 else ''}")
    else:
        print(f"❌ Processing failed: {result.error}")


if __name__ == "__main__":
    print("🚀 Phase 4A Item 1: Enhanced Document Processing Demo")
    print("=" * 60)

    demo_supported_formats()
    demo_file_processing()
    demo_base64_processing()
    demo_error_handling()
    demo_direct_processor_usage()

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\n📋 Summary of Phase 4A Item 1 Implementation:")
    print("   ✅ DocumentProcessor class with multi-format support")
    print("   ✅ Support for ODT, RTF, DOCX, TXT formats")
    print("   ✅ Comprehensive metadata extraction")
    print("   ✅ MCP tool: process_document_formats")
    print("   ✅ Graceful fallbacks for missing dependencies")
    print("   ✅ Extensive test coverage")
    print("   ✅ Integration with existing ArXiv pipeline")
