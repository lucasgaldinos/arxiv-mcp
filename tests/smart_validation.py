"""
Smart validation script for the implemented priority features.
Tests real functionality rather than just making tests pass.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_citation_extraction_real():
    """Test real citation extraction with academic text."""
    from arxiv_mcp.utils.citations import CitationParser

    parser = CitationParser()

    # Real academic text with clear citations
    academic_text = """
    References

    [1] Smith, J., & Johnson, A. (2023). Machine Learning Fundamentals. Journal of AI Research, 45(2), 123-145.

    [2] Brown, M. et al. (2022). "Deep Learning Applications in Natural Language Processing."
        Proceedings of ICML 2022, pp. 67-89.

    [3] Wilson, K. (2021). Statistical Methods for Data Science. MIT Press, Cambridge, MA.
    """

    citations = parser.extract_citations(academic_text)

    print(f"✓ Citation extraction test:")
    print(f"  - Found {len(citations)} citations")
    print(f"  - Expected at least 2 citations from the references section")

    for i, citation in enumerate(citations):
        print(f"  - Citation {i + 1}: {citation.title[:50]}...")
        print(f"    Authors: {citation.authors}")
        print(f"    Year: {citation.year}")
        print(f"    Confidence: {citation.confidence:.2f}")

    return len(citations) >= 2


def test_optional_dependencies_real():
    """Test optional dependencies functionality."""
    from arxiv_mcp.utils.optional_deps import get_available_features, optional_import

    features = get_available_features()

    print(f"✓ Optional dependencies test:")
    print(f"  - Total optional packages checked: {len(features)}")

    available_count = sum(1 for available in features.values() if available)
    print(f"  - Available packages: {available_count}")
    print(f"  - Missing packages: {len(features) - available_count}")

    # Test graceful fallback
    try:
        nltk_dep = optional_import("nltk")
        print(f"  - NLTK available: {nltk_dep.available}")
        if not nltk_dep.available:
            print(f"    Fallback working correctly")
    except Exception as e:
        print(f"  - Error in optional dependency handling: {e}")
        return False

    return True


def test_docs_generation_real():
    """Test real documentation generation."""
    from arxiv_mcp.utils.docs_generator import generate_api_docs
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Generate docs in temporary directory
            docs = generate_api_docs(output_path=temp_dir, formats=["json"])

            print(f"✓ Documentation generation test:")
            print(f"  - Generated documentation for {len(docs.modules)} modules")
            print(f"  - Found {len(docs.tools_summary or [])} MCP tools")
            print(f"  - Documentation title: {docs.title}")
            print(f"  - Version: {docs.version}")

            # Validate documentation structure
            required_modules = ["tools", "citations", "optional_deps", "docs_generator"]
            found_modules = [m.name for m in docs.modules]

            for required in required_modules:
                if any(required in name for name in found_modules):
                    print(f"  ✓ Found {required} module documentation")
                else:
                    print(f"  ✗ Missing {required} module documentation")

            return len(docs.modules) >= 4 and len(docs.tools_summary or []) >= 5

        except Exception as e:
            print(f"  - Error generating documentation: {e}")
            return False


def test_mcp_tools_integration():
    """Test that MCP tools can be imported and have correct structure."""
    try:
        # Add src to path for relative imports
        import sys
        import os

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

        from arxiv_mcp.tools import get_tools

        tools = get_tools()

        print(f"✓ MCP tools integration test:")
        print(f"  - Total tools available: {len(tools)}")

        # Check for our new tools
        expected_tools = [
            "extract_citations",
            "parse_citations_from_arxiv",
            "generate_api_docs",
        ]
        found_tools = [tool.name for tool in tools]

        for expected in expected_tools:
            if expected in found_tools:
                print(f"  ✓ Found tool: {expected}")
            else:
                print(f"  ✗ Missing tool: {expected}")

        # Validate tool structure
        for tool in tools[:3]:  # Check first few tools
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

        return len([t for t in expected_tools if t in found_tools]) >= 2

    except Exception as e:
        print(f"  - Error testing MCP tools: {e}")
        return False


def test_real_workflow():
    """Test a complete workflow using our features."""
    print(f"✓ Complete workflow test:")

    try:
        # 1. Check optional dependencies
        from arxiv_mcp.utils.optional_deps import get_available_features

        features = get_available_features()
        print(f"  - Dependency check: {len(features)} packages evaluated")

        # 2. Extract citations from sample text
        from arxiv_mcp.utils.citations import CitationParser, CitationFormat

        parser = CitationParser()

        sample_text = """
        Smith, J. (2023). "AI Research Methods." Nature AI, 5(3), 45-67.
        Brown, A., & Wilson, B. (2022). Deep Learning Handbook. MIT Press.
        """

        citations = parser.extract_citations(sample_text)
        print(f"  - Citation extraction: {len(citations)} citations found")

        # 3. Format citations
        if citations:
            bibtex = parser.format_citation(citations[0], CitationFormat.BIBTEX)
            print(f"  - Citation formatting: BibTeX generated ({len(bibtex)} chars)")

        # 4. Generate documentation
        from arxiv_mcp.utils.docs_generator import generate_api_docs
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            docs = generate_api_docs(output_path=temp_dir, formats=["markdown"])
            print(f"  - Documentation: {len(docs.modules)} modules documented")

        return True

    except Exception as e:
        print(f"  - Workflow error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Smart validation of implemented priority features\n")

    tests = [
        ("Citation Extraction", test_citation_extraction_real),
        ("Optional Dependencies", test_optional_dependencies_real),
        ("Documentation Generation", test_docs_generation_real),
        ("MCP Tools Integration", test_mcp_tools_integration),
        ("Complete Workflow", test_real_workflow),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Testing: {test_name}")
        print(f"{'=' * 60}")

        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\nResult: {status}")

        except Exception as e:
            results[test_name] = False
            print(f"\nResult: ❌ ERROR - {e}")

    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 60}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All priority features are working correctly!")
    else:
        print("⚠️  Some features need attention")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
