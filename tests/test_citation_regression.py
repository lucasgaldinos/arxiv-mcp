"""
Edge case regression tests for citation extraction fixes.
Tests specific issues identified and fixed in Task 1.
Created as part of Group 1 Critical Fixes Task 3.
"""

import pytest

from arxiv_mcp.utils.citations import CitationParser


class TestTask1RegressionSuite:
    """Regression tests for specific Task 1 fixes."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_title_extraction_patterns(self):
        """Test the three title extraction patterns that were failing."""

        # Pattern 1: Basic title extraction
        citation1 = """
References

[1] Smith, J. (2020). Simple title here. Journal Name.
"""

        # Pattern 2: Title with colon
        citation2 = """
References

[1] Jones, M. (2021). Complex title: A detailed study of something important.
Research Journal, 15(3), 123-145.
"""

        # Pattern 3: ArXiv preprint format
        citation3 = """
References

[1] Brown, A. (2022). Machine learning advances. arXiv preprint arXiv:2201.12345.
"""

        # Test each pattern
        results1 = self.parser.extract_citations(citation1)
        results2 = self.parser.extract_citations(citation2)
        results3 = self.parser.extract_citations(citation3)

        # All should extract titles successfully
        assert len(results1) == 1 and results1[0].title == "Simple title here"
        assert len(results2) == 1 and "Complex title: A detailed study" in results2[0].title
        assert len(results3) == 1 and results3[0].title == "Machine learning advances"

    def test_author_parsing_artifacts(self):
        """Test that author parsing artifacts are eliminated."""

        # This citation was producing "A In" artifacts
        problematic_citation = """
References

[1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... &
Polosukhin, I. (2017). Attention is all you need. In Advances in neural information
processing systems (pp. 5998-6008).
"""

        citations = self.parser.extract_citations(problematic_citation)
        assert len(citations) == 1

        citation = citations[0]
        all_authors = citation.authors

        # Should not contain parsing artifacts
        assert "A In" not in all_authors
        assert "In Advances" not in all_authors
        assert "Information Processing" not in all_authors

        # Should contain actual authors
        assert "Vaswani, A." in all_authors
        assert "Polosukhin, I." in all_authors

    def test_ellipsis_handling(self):
        """Test proper handling of ellipsis in author lists."""

        ellipsis_citation = """
References

[1] First, A., Second, B., Third, C., ... & Last, Z. (2023). Paper with many authors.
Journal of Collaborative Research, 10(1), 1-20.
"""

        citations = self.parser.extract_citations(ellipsis_citation)
        assert len(citations) == 1

        citation = citations[0]
        authors = citation.authors

        # Should include first authors and last author
        assert "First, A." in authors
        assert "Second, B." in authors
        assert "Last, Z." in authors

        # Should not include ellipsis as an author
        assert "..." not in authors
        assert "et al" not in authors

    def test_confidence_improvement(self):
        """Test that confidence scores meet the 0.85+ target."""

        # Use the exact citations that were tested in Task 1
        test_citations = """
References

[1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... &
Polosukhin, I. (2017). Attention is all you need. In Advances in neural information
processing systems (pp. 5998-6008).

[2] Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep
bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.

[3] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., ... &
Amodei, D. (2020). Language models are few-shot learners. Advances in neural information
processing systems, 33, 1877-1902.
"""

        citations = self.parser.extract_citations(test_citations)
        assert len(citations) == 3

        # Calculate average confidence
        confidences = [c.confidence for c in citations if hasattr(c, "confidence")]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            assert (
                avg_confidence >= 0.85
            ), f"Average confidence {avg_confidence:.3f} below target 0.85"

    def test_three_out_of_three_extraction(self):
        """Test that all 3 citations are properly extracted (was 1/3 before fix)."""

        original_failing_case = """
References

[1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... &
Polosukhin, I. (2017). Attention is all you need. In Advances in neural information
processing systems (pp. 5998-6008).

[2] Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep
bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.

[3] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., ... &
Amodei, D. (2020). Language models are few-shot learners. Advances in neural information
processing systems, 33, 1877-1902.
"""

        citations = self.parser.extract_citations(original_failing_case)

        # This should now be 3/3 instead of 1/3
        assert len(citations) == 3, f"Expected 3 citations, got {len(citations)}"

        # All should have titles
        titles = [c.title for c in citations if c.title and len(c.title.strip()) > 5]
        assert len(titles) == 3, f"Expected 3 titles, got {len(titles)}"

        # All should have authors
        citations_with_authors = [c for c in citations if c.authors and len(c.authors) > 0]
        assert (
            len(citations_with_authors) == 3
        ), f"Expected 3 citations with authors, got {len(citations_with_authors)}"

    def test_specific_title_extractions(self):
        """Test specific titles that were not being extracted."""

        # These specific titles were problematic
        test_cases = [
            {
                "citation": """[1] Vaswani, A. et al. (2017). Attention is all you need. In Advances in neural information processing systems.""",
                "expected_title": "Attention is all you need",
            },
            {
                "citation": """[2] Devlin, J. et al. (2018). BERT: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.""",
                "expected_title": "BERT: Pre-training of deep bidirectional transformers for language understanding",
            },
            {
                "citation": """[3] Brown, T. et al. (2020). Language models are few-shot learners. Advances in neural information processing systems.""",
                "expected_title": "Language models are few-shot learners",
            },
        ]

        for i, test_case in enumerate(test_cases):
            test_doc = f"References\n\n{test_case['citation']}"
            citations = self.parser.extract_citations(test_doc)

            assert (
                len(citations) == 1
            ), f"Test case {i + 1}: Expected 1 citation, got {len(citations)}"

            extracted_title = citations[0].title
            expected_title = test_case["expected_title"]

            assert (
                extracted_title == expected_title
            ), f"Test case {i + 1}: Expected title '{expected_title}', got '{extracted_title}'"

    def test_journal_vs_arxiv_format_detection(self):
        """Test proper detection of journal vs arXiv formats."""

        journal_citation = """
References

[1] Smith, J. (2020). Journal paper title. Nature, 580(7805), 612-616.
"""

        arxiv_citation = """
References

[1] Jones, M. (2021). ArXiv paper title. arXiv preprint arXiv:2101.12345.
"""

        journal_results = self.parser.extract_citations(journal_citation)
        arxiv_results = self.parser.extract_citations(arxiv_citation)

        assert len(journal_results) == 1
        assert len(arxiv_results) == 1

        # Both should extract titles properly
        assert journal_results[0].title == "Journal paper title"
        assert arxiv_results[0].title == "ArXiv paper title"

        # Both should have proper confidence
        assert journal_results[0].confidence >= 0.8
        assert arxiv_results[0].confidence >= 0.8

    def test_multiline_citation_handling(self):
        """Test handling of citations spanning multiple lines."""

        multiline_citation = """
References

[1] Very, Long, List, Of, Authors, A., Even, More, Authors, B., And, Yet, More, C.
(2023). This is a very long title that spans multiple lines and contains many
technical terms and detailed descriptions of the research methodology.
Journal of Very Long Papers and Extensive Details, 15(3), 123-145.
"""

        citations = self.parser.extract_citations(multiline_citation)
        assert len(citations) == 1

        citation = citations[0]

        # Should extract title from multiple lines
        assert "This is a very long title" in citation.title
        assert "methodology" in citation.title

        # Should extract authors
        assert len(citation.authors) > 0
        assert "Very, Long" in citation.authors[0]  # First author

        # Should have reasonable confidence
        assert citation.confidence >= 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
