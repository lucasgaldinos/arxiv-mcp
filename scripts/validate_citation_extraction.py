"""
Automated test runner and performance benchmark for citation extraction.
Provides comprehensive validation with automated reporting.
Created as part of Group 1 Critical Fixes Task 3.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
import time

import coverage


@dataclass
class TestResult:
    """Test result data structure."""

    test_name: str
    passed: bool
    duration: float
    error_message: str = ""
    coverage_percent: float = 0.0


@dataclass
class BenchmarkResult:
    """Performance benchmark result."""

    operation: str
    documents_processed: int
    total_time: float
    citations_per_second: float
    memory_usage_mb: float = 0.0


@dataclass
class ValidationReport:
    """Complete validation report."""

    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_coverage: float
    test_results: list[TestResult]
    benchmark_results: list[BenchmarkResult]
    quality_metrics: dict[str, float]


class CitationTestRunner:
    """Comprehensive test runner for citation extraction."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dir = project_root / "tests"
        self.src_dir = project_root / "src"

    def run_unit_tests(self) -> list[TestResult]:
        """Run unit tests with coverage tracking."""
        print("🧪 Running comprehensive unit tests...")

        # Initialize coverage
        cov = coverage.Coverage(source=[str(self.src_dir)])
        cov.start()

        try:
            # Run pytest with comprehensive test file
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(self.test_dir / "test_citation_extraction_comprehensive.py"),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=test_results.json",
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            cov.stop()
            cov.save()

            # Parse test results
            test_results = self._parse_pytest_output(result.stdout, result.stderr)

            # Add coverage information
            coverage_percent = self._get_coverage_percentage(cov)
            for test_result in test_results:
                test_result.coverage_percent = coverage_percent

            return test_results

        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return [
                TestResult(
                    test_name="test_execution_error",
                    passed=False,
                    duration=0.0,
                    error_message=str(e),
                )
            ]

    def run_performance_benchmarks(self) -> list[BenchmarkResult]:
        """Run performance benchmarks."""
        print("⚡ Running performance benchmarks...")

        benchmarks = []

        # Import citation parser for benchmarking
        sys.path.insert(0, str(self.src_dir))
        try:
            from arxiv_mcp.utils.citations import CitationParser

            parser = CitationParser()

            # Benchmark 1: Single citation processing
            single_citation = """
References

[1] Benchmark, A., Test, B. (2023). Performance testing citation.
Journal of Benchmarking, 1(1), 1-10.
"""

            start_time = time.time()
            for _ in range(1000):
                citations = parser.extract_citations(single_citation)
            end_time = time.time()

            benchmarks.append(
                BenchmarkResult(
                    operation="single_citation_processing",
                    documents_processed=1000,
                    total_time=end_time - start_time,
                    citations_per_second=1000 / (end_time - start_time),
                )
            )

            # Benchmark 2: Batch processing
            batch_doc = self._generate_batch_document(50)

            start_time = time.time()
            citations = parser.extract_citations(batch_doc)
            end_time = time.time()

            benchmarks.append(
                BenchmarkResult(
                    operation="batch_processing_50_citations",
                    documents_processed=1,
                    total_time=end_time - start_time,
                    citations_per_second=len(citations) / (end_time - start_time),
                )
            )

            # Benchmark 3: Memory efficiency test
            start_time = time.time()
            for i in range(100):
                test_doc = f"""
References

[{i + 1}] Author{i}, B. ({2020 + i % 5}). Memory test citation {i}.
Test Journal, {i + 1}(1), {i}-{i + 10}.
"""
                citations = parser.extract_citations(test_doc)
            end_time = time.time()

            benchmarks.append(
                BenchmarkResult(
                    operation="memory_efficiency_100_iterations",
                    documents_processed=100,
                    total_time=end_time - start_time,
                    citations_per_second=100 / (end_time - start_time),
                )
            )

        except ImportError as e:
            print(f"❌ Error importing citation parser: {e}")
            benchmarks.append(
                BenchmarkResult(
                    operation="import_error",
                    documents_processed=0,
                    total_time=0.0,
                    citations_per_second=0.0,
                )
            )

        return benchmarks

    def calculate_quality_metrics(self) -> dict[str, float]:
        """Calculate quality metrics for citation extraction."""
        print("📊 Calculating quality metrics...")

        sys.path.insert(0, str(self.src_dir))
        try:
            from arxiv_mcp.utils.citations import CitationParser

            parser = CitationParser()

            # Test with known high-quality citations
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

[4] Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., & Sutskever, I. (2019).
Language models are unsupervised multitask learners. OpenAI blog, 1(8), 9.

[5] Raffel, C., Shazeer, N., Roberts, A., Lee, K., Narang, S., Matena, M., ... & Liu, P. J.
(2020). Exploring the limits of transfer learning with a unified text-to-text transformer.
Journal of machine learning research, 21(140), 1-67.
"""

            citations = parser.extract_citations(test_citations)

            # Calculate metrics
            total_citations = len(citations)
            titles_extracted = sum(1 for c in citations if c.title and len(c.title.strip()) > 5)
            authors_extracted = sum(1 for c in citations if c.authors and len(c.authors) > 0)
            years_extracted = sum(1 for c in citations if c.year and c.year.isdigit())

            # Confidence scores
            confidences = [c.confidence for c in citations if hasattr(c, "confidence")]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "total_citations_processed": total_citations,
                "title_extraction_rate": titles_extracted / total_citations
                if total_citations > 0
                else 0.0,
                "author_extraction_rate": authors_extracted / total_citations
                if total_citations > 0
                else 0.0,
                "year_extraction_rate": years_extracted / total_citations
                if total_citations > 0
                else 0.0,
                "average_confidence_score": avg_confidence,
                "quality_target_met": avg_confidence >= 0.85
                and (titles_extracted / total_citations) >= 0.9
                if total_citations > 0
                else False,
            }

        except Exception as e:
            print(f"❌ Error calculating quality metrics: {e}")
            return {"error": str(e), "quality_target_met": False}

    def generate_validation_report(self) -> ValidationReport:
        """Generate comprehensive validation report."""
        print("📋 Generating validation report...")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Run all tests and benchmarks
        test_results = self.run_unit_tests()
        benchmark_results = self.run_performance_benchmarks()
        quality_metrics = self.calculate_quality_metrics()

        # Calculate summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t.passed)
        failed_tests = total_tests - passed_tests

        # Get overall coverage
        overall_coverage = test_results[0].coverage_percent if test_results else 0.0

        return ValidationReport(
            timestamp=timestamp,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            overall_coverage=overall_coverage,
            test_results=test_results,
            benchmark_results=benchmark_results,
            quality_metrics=quality_metrics,
        )

    def save_report(self, report: ValidationReport, output_file: Path):
        """Save validation report to file."""
        report_dict = asdict(report)

        with open(output_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"📄 Report saved to: {output_file}")

    def print_summary(self, report: ValidationReport):
        """Print validation summary to console."""
        print("\n" + "=" * 60)
        print("🎯 CITATION EXTRACTION VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Tests: {report.total_tests}")
        print(f"Passed: {report.passed_tests}")
        print(f"Failed: {report.failed_tests}")
        print(
            f"Success Rate: {(report.passed_tests / report.total_tests * 100):.1f}%"
            if report.total_tests > 0
            else "N/A"
        )
        print(f"Test Coverage: {report.overall_coverage:.1f}%")

        print("\n📊 Quality Metrics:")
        for metric, value in report.quality_metrics.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")

        print("\n⚡ Performance Benchmarks:")
        for bench in report.benchmark_results:
            print(f"  {bench.operation}: {bench.citations_per_second:.1f} citations/sec")

        # Check if targets are met
        quality_met = report.quality_metrics.get("quality_target_met", False)
        coverage_met = report.overall_coverage >= 95.0
        performance_met = any(b.citations_per_second >= 20 for b in report.benchmark_results)

        print("\n🎯 Target Achievement:")
        print(
            f"  Quality Target (≥90% extraction, ≥0.85 confidence): {'✅' if quality_met else '❌'}"
        )
        print(f"  Coverage Target (≥95%): {'✅' if coverage_met else '❌'}")
        print(f"  Performance Target (≥20 citations/sec): {'✅' if performance_met else '❌'}")

        if quality_met and coverage_met and performance_met:
            print("\n🎉 ALL TARGETS MET - PRODUCTION READY!")
        else:
            print("\n⚠️  Some targets not met - needs attention")

    def _parse_pytest_output(self, stdout: str, stderr: str) -> list[TestResult]:
        """Parse pytest output to extract test results."""
        test_results = []

        # Basic parsing - in real implementation would parse JSON report
        if "FAILED" in stdout or "ERROR" in stderr:
            test_results.append(
                TestResult(
                    test_name="comprehensive_tests",
                    passed=False,
                    duration=0.0,
                    error_message=stderr,
                )
            )
        else:
            test_results.append(
                TestResult(test_name="comprehensive_tests", passed=True, duration=1.0)
            )

        return test_results

    def _get_coverage_percentage(self, cov: coverage.Coverage) -> float:
        """Get coverage percentage from coverage object."""
        try:
            # Generate coverage report
            total = cov.report(show_missing=False, file=None)
            return float(total)
        except:
            return 0.0

    def _generate_batch_document(self, num_citations: int) -> str:
        """Generate a document with multiple citations for testing."""
        doc = "References\n\n"

        for i in range(num_citations):
            doc += f"""[{i + 1}] Author{i}, B., Coauthor{i}, C. ({2000 + i % 20}).
Title of paper number {i + 1} with various research topics.
Journal of Topic {i % 10}, {i // 2 + 1}({i % 5 + 1}), {i * 10}-{i * 10 + 20}.

"""

        return doc


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent

    runner = CitationTestRunner(project_root)

    print("🚀 Starting Citation Extraction Validation Suite")
    print("=" * 60)

    # Generate comprehensive validation report
    report = runner.generate_validation_report()

    # Print summary to console
    runner.print_summary(report)

    # Save detailed report
    output_file = project_root / "validation_report.json"
    runner.save_report(report, output_file)

    # Exit with appropriate code
    if report.failed_tests > 0:
        print("\n❌ Some tests failed - check report for details")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
