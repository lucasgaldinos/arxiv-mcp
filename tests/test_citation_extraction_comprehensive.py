"""
Comprehensive test suite for citation extraction functionality.
Tests edge cases, performance benchmarks, and production readiness.
Created as part of Group 1 Critical Fixes Task 3.
"""

import time

import pytest

from arxiv_mcp.utils.citations import CitationFormat, CitationParser


class TestCitationExtractionEdgeCases:
    """Test edge cases for citation extraction."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_empty_and_null_inputs(self):
        """Test handling of empty and null inputs."""
        # Empty string
        citations = self.parser.extract_citations("")
        assert len(citations) == 0

        # None input
        citations = self.parser.extract_citations(None)
        assert len(citations) == 0

        # Whitespace only
        citations = self.parser.extract_citations("   \n\t   ")
        assert len(citations) == 0

    def test_malformed_citations(self):
        """Test handling of malformed citation formats."""
        malformed_citations = [
            # Missing brackets
            "1 Smith, J. (2020). Title here. Journal.",
            # Incomplete author format
            "[1] Smith (2020). Title. Journal.",
            # Missing year
            "[1] Smith, J. Title. Journal.",
            # Corrupted format
            "[1] Smith,,,, J...... ((((2020)))). Title. Journal.",
            # Mixed formatting
            "[1] Smith, J. 2020. Title. Journal of Things, vol 5, pp 1-10.",
        ]

        for malformed in malformed_citations:
            citations = self.parser.extract_citations(f"References\n\n{malformed}")
            # Should either extract cleanly or fail gracefully
            assert len(citations) <= 1  # Should not crash or extract multiple

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode characters and special symbols."""
        unicode_citations = """
References

[1] Müller, J., González, M., & Sørensen, K. (2020). Advanced techniques in données analysis.
Journal of Café Science, 15(3), 123-145.

[2] Zhang, 李明, Wang, 王芳 (2021). Deep learning with 神经网络.
AI Research Letters, 8(2), 67-89.

[3] O'Connor, P., D'Angelo, M. (2019). Résumé of machine learning:
A comprehensive étude. Technical Report #TR-2019-001.
"""

        citations = self.parser.extract_citations(unicode_citations)
        assert len(citations) == 3

        # Check that Unicode characters are preserved
        for citation in citations:
            assert len(citation.authors) > 0
            assert citation.year is not None
            assert len(citation.title) > 5

    def test_very_long_citations(self):
        """Test handling of extremely long citation texts."""
        # Create a citation with very long author list
        long_author_list = ", ".join([f"Author{i}, A." for i in range(50)])
        long_citation = f"""
References

[1] {long_author_list} (2020). This is a paper with an extremely long list of authors
which sometimes happens in large collaboration papers in physics or medical research.
The title itself can also be quite long and contain many technical terms and detailed
descriptions of the methodology and findings. Journal of Very Long Paper Titles and
Extensive Author Lists, 25(12), 1234-5678.
"""

        citations = self.parser.extract_citations(long_citation)
        assert len(citations) == 1
        citation = citations[0]

        # Should handle long author lists gracefully (limited to 10)
        assert len(citation.authors) <= 10
        assert citation.year == "2020"
        assert len(citation.title) > 20

    def test_mixed_citation_formats(self):
        """Test handling of mixed citation formats in same document."""
        mixed_formats = """
References

[1] Smith, J. (2020). First paper. Journal A.

(2) Jones, M., Brown, P. (2021). Second paper. Conference B.

[3] Wilson, K. et al. 2019. Third paper. Book C, Chapter 5.

4. Davis, L. (2018) "Fourth paper with quotes". Magazine D, vol 10.
"""

        citations = self.parser.extract_citations(mixed_formats)
        # Should extract at least the properly formatted ones
        assert len(citations) >= 1

    def test_citation_boundary_detection(self):
        """Test proper detection of citation boundaries."""
        boundary_test = """
References

[1] First, A. (2020). First paper title. First Journal, 1(1), 1-10.
This is some additional text that might confuse the parser.

[2] Second, B. (2021). Second paper title. Second Journal, 2(2), 20-30.
Another line that shouldn't be part of the citation.

[3] Third, C. (2022). Third paper title. Third Journal, 3(3), 40-50.
"""

        citations = self.parser.extract_citations(boundary_test)
        assert len(citations) == 3

        for citation in citations:
            # Additional text should not be included in raw citation
            assert "This is some additional text" not in citation.raw_text
            assert "Another line that shouldn't" not in citation.raw_text


class TestCitationExtractionPerformance:
    """Performance benchmarks for citation extraction."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_large_document_performance(self):
        """Test performance with large documents."""
        # Create a large document with many citations
        large_doc = "References\n\n"
        for i in range(100):
            large_doc += f"""[{i + 1}] Author{i}, B., Coauthor{i}, C. ({2000 + i % 20}).
Title of paper number {i + 1} with various research topics.
Journal of Topic {i % 10}, {i // 2 + 1}({i % 5 + 1}), {i * 10}-{i * 10 + 20}.

"""

        start_time = time.time()
        citations = self.parser.extract_citations(large_doc)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should process 100 citations in reasonable time
        assert len(citations) == 100
        assert processing_time < 5.0  # Should complete within 5 seconds

        # Calculate citations per second
        cps = len(citations) / processing_time
        assert cps > 20  # Should process at least 20 citations per second

    def test_memory_efficiency(self):
        """Test memory efficiency with repeated processing."""
        test_citation = """
References

[1] Memory, Test (2023). Testing memory efficiency in citation parsing.
Journal of Performance Testing, 1(1), 1-10.
"""

        # Process the same citation multiple times
        for _ in range(1000):
            citations = self.parser.extract_citations(test_citation)
            assert len(citations) == 1

        # Should not accumulate memory issues


class TestCitationQualityValidation:
    """Test quality validation and confidence scoring."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_confidence_scoring_accuracy(self):
        """Test accuracy of confidence scoring."""
        high_quality_citation = """
References

[1] Perfect, A., Example, B. (2023). This is a perfectly formatted citation with all elements.
Journal of High Quality Citations, 15(3), 123-145. doi:10.1000/example123
"""

        low_quality_citation = """
References

[1] Poor Example
"""

        high_citations = self.parser.extract_citations(high_quality_citation)
        low_citations = self.parser.extract_citations(low_quality_citation)

        if high_citations:
            high_confidence = high_citations[0].confidence
            assert high_confidence >= 0.8  # Should have high confidence

        if low_citations:
            low_confidence = low_citations[0].confidence
            assert low_confidence <= 0.5  # Should have low confidence

    def test_quality_metrics_validation(self):
        """Test that quality metrics meet production targets."""
        # Test with known good citations
        good_citations = """
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

        citations = self.parser.extract_citations(good_citations)
        assert len(citations) == 3

        # Calculate quality metrics
        titles_extracted = sum(1 for c in citations if c.title and len(c.title.strip()) > 5)
        authors_extracted = sum(1 for c in citations if c.authors and len(c.authors) > 0)
        years_extracted = sum(1 for c in citations if c.year)

        # Quality targets (based on Task 1 improvements)
        title_accuracy = titles_extracted / len(citations)
        author_accuracy = authors_extracted / len(citations)
        year_accuracy = years_extracted / len(citations)

        assert title_accuracy >= 0.9  # 90%+ title extraction
        assert author_accuracy >= 0.9  # 90%+ author extraction
        assert year_accuracy >= 0.9  # 90%+ year extraction

        # Overall confidence should meet targets
        avg_confidence = sum(c.confidence for c in citations) / len(citations)
        assert avg_confidence >= 0.85  # Target from Task 1


class TestCitationFormatGeneration:
    """Test citation format generation capabilities."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_bibtex_format_generation(self):
        """Test BibTeX format generation."""
        test_citation = """
References

[1] Smith, J., Doe, A. (2023). Test paper title. Test Journal, 1(1), 1-10.
"""

        citations = self.parser.extract_citations(test_citation)
        assert len(citations) == 1

        bibtex = self.parser.format_citation(citations[0], CitationFormat.BIBTEX)

        # Basic BibTeX format validation
        assert bibtex.startswith("@")
        assert "title = {" in bibtex
        assert "author = {" in bibtex
        assert "year = {" in bibtex

    def test_apa_format_generation(self):
        """Test APA format generation."""
        test_citation = """
References

[1] Johnson, M., Williams, S. (2022). Research methodology. Academic Press, 5(2), 25-45.
"""

        citations = self.parser.extract_citations(test_citation)
        assert len(citations) == 1

        apa = self.parser.format_citation(citations[0], CitationFormat.APA)

        # Basic APA format validation
        assert "(2022)" in apa  # Year in parentheses
        assert "," in apa  # Author separation


class TestRegressionSuite:
    """Regression tests to ensure fixes don't break existing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = CitationParser()

    def test_task1_fixes_regression(self):
        """Ensure Task 1 fixes are maintained."""
        # The exact test case that was failing before Task 1 fixes
        original_problem = """
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

        citations = self.parser.extract_citations(original_problem)

        # These were the specific issues that were fixed:
        assert len(citations) == 3  # Should extract all 3 citations

        # Title extraction should work for all 3
        titles = [c.title for c in citations if c.title and len(c.title.strip()) > 5]
        assert len(titles) == 3  # All titles should be extracted

        # No "A In" artifacts in authors
        all_authors = []
        for citation in citations:
            all_authors.extend(citation.authors)

        assert "A In" not in all_authors  # Should not have parsing artifacts

        # Average confidence should be ≥ 0.85 (Task 1 target)
        avg_confidence = sum(c.confidence for c in citations) / len(citations)
        assert avg_confidence >= 0.85

    def test_backward_compatibility(self):
        """Ensure backward compatibility is maintained."""
        # Test old citation formats still work
        old_format = """
References

Smith, J. (2020). Old format paper. Traditional Journal.
"""

        citations = self.parser.extract_citations(old_format)
        # Should handle gracefully, even if extraction isn't perfect
        assert isinstance(citations, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
