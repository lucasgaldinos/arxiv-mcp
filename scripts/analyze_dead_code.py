#!/usr/bin/env python3
"""
Dead Code Analysis Script for ArXiv MCP Server

This script automates the detection and reporting of unused code including:
- Unused imports (autoflake)
- Unused functions/classes/variables (vulture)
- Unreachable code
- Obsolete test files

Usage:
    python scripts/analyze_dead_code.py [--fix] [--report-only]
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys


class DeadCodeAnalyzer:
    """Automated dead code analysis and cleanup tool."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.src_dirs = ["src/", "tests/", "scripts/"]
        self.results = {
            "vulture_findings": [],
            "autoflake_findings": [],
            "summary": {},
            "timestamp": datetime.now().isoformat(),
        }

    def run_vulture_analysis(self) -> list[str]:
        """Run vulture to detect unused code."""
        print("🔍 Running vulture analysis for unused code...")

        cmd = ["uv", "run", "vulture", "--min-confidence", "80", "--sort-by-size"] + self.src_dirs

        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=self.repo_root)

            if result.stdout:
                findings = result.stdout.strip().split("\n")
                self.results["vulture_findings"] = [f for f in findings if f.strip()]
                print(f"   Found {len(self.results['vulture_findings'])} unused code issues")
                return self.results["vulture_findings"]
            print("   ✅ No unused code detected by vulture")
            return []

        except subprocess.CalledProcessError as e:
            print(f"   ❌ Vulture analysis failed: {e}")
            return []

    def run_autoflake_analysis(self) -> dict[str, list[str]]:
        """Run autoflake to detect unused imports."""
        print("🔍 Running autoflake analysis for unused imports...")

        findings = {}

        for src_dir in self.src_dirs:
            cmd = [
                "uv",
                "run",
                "autoflake",
                "--check",
                "--recursive",
                "--remove-unused-variables",
                "--remove-all-unused-imports",
                src_dir,
            ]

            try:
                result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=self.repo_root)

                if result.stdout:
                    lines = [line.strip() for line in result.stdout.split("\n") if line.strip()]
                    problematic_files = [
                        line.split(":")[0]
                        for line in lines
                        if "Unused imports/variables detected" in line
                    ]
                    if problematic_files:
                        findings[src_dir] = problematic_files

            except subprocess.CalledProcessError as e:
                print(f"   ❌ Autoflake analysis failed for {src_dir}: {e}")

        self.results["autoflake_findings"] = findings
        total_files = sum(len(files) for files in findings.values())
        print(f"   Found {total_files} files with unused imports/variables")

        return findings

    def categorize_findings(self) -> dict[str, list[str]]:
        """Categorize findings by severity and type."""
        categories = {
            "critical_unused_imports": [],
            "unused_functions_classes": [],
            "unreachable_code": [],
            "test_cleanup_needed": [],
            "low_priority": [],
        }

        for finding in self.results["vulture_findings"]:
            if "unused import" in finding.lower():
                categories["critical_unused_imports"].append(finding)
            elif "unreachable code" in finding.lower():
                categories["unreachable_code"].append(finding)
            elif any(test_dir in finding for test_dir in ["tests/", "test_"]):
                categories["test_cleanup_needed"].append(finding)
            elif any(
                keyword in finding.lower()
                for keyword in ["unused function", "unused class", "unused method"]
            ):
                categories["unused_functions_classes"].append(finding)
            else:
                categories["low_priority"].append(finding)

        return categories

    def generate_report(self) -> str:
        """Generate a comprehensive dead code analysis report."""
        categories = self.categorize_findings()

        report = [
            "# Dead Code Analysis Report",
            f"Generated: {self.results['timestamp']}",
            f"Repository: {self.repo_root.name}",
            "",
            "## Summary",
            f"- Vulture findings: {len(self.results['vulture_findings'])}",
            f"- Files with unused imports: {sum(len(files) for files in self.results['autoflake_findings'].values())}",
            "",
        ]

        # Critical issues first
        if categories["critical_unused_imports"]:
            report.extend(["## 🔴 Critical: Unused Imports", ""])
            for finding in categories["critical_unused_imports"]:
                report.append(f"- `{finding}`")
            report.append("")

        if categories["unreachable_code"]:
            report.extend(["## 🔴 Critical: Unreachable Code", ""])
            for finding in categories["unreachable_code"]:
                report.append(f"- `{finding}`")
            report.append("")

        # Unused functions/classes
        if categories["unused_functions_classes"]:
            report.extend(["## 🟡 Medium: Unused Functions/Classes", ""])
            for finding in categories["unused_functions_classes"]:
                report.append(f"- `{finding}`")
            report.append("")

        # Test cleanup
        if categories["test_cleanup_needed"]:
            report.extend(["## 🟡 Medium: Test Cleanup Needed", ""])
            for finding in categories["test_cleanup_needed"]:
                report.append(f"- `{finding}`")
            report.append("")

        # Autoflake findings
        if self.results["autoflake_findings"]:
            report.extend(["## 📁 Files with Unused Imports/Variables", ""])
            for src_dir, files in self.results["autoflake_findings"].items():
                if files:
                    report.append(f"### {src_dir}")
                    for file in files:
                        report.append(f"- `{file}`")
                    report.append("")

        # Recommendations
        report.extend(
            [
                "## 🛠️ Recommended Actions",
                "",
                "### Immediate (Critical)",
                "1. Run `autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports src/ tests/ scripts/`",
                "2. Fix unreachable code manually",
                "3. Remove critical unused imports",
                "",
                "### Next Steps (Medium Priority)",
                "1. Review and remove unused functions/classes (verify they're truly unused)",
                "2. Clean up test files and obsolete test fixtures",
                "3. Add vulture configuration to ignore false positives",
                "",
                "### Automation",
                "1. Add autoflake to pre-commit hooks",
                "2. Add vulture analysis to CI pipeline",
                "3. Set up regular dead code analysis schedule",
                "",
            ]
        )

        return "\n".join(report)

    def auto_fix_imports(self) -> bool:
        """Automatically fix unused imports using autoflake."""
        print("🔧 Automatically fixing unused imports...")

        cmd = [
            "uv",
            "run",
            "autoflake",
            "--in-place",
            "--recursive",
            "--remove-unused-variables",
            "--remove-all-unused-imports",
        ] + self.src_dirs

        try:
            result = subprocess.run(cmd, check=False, cwd=self.repo_root, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Unused imports fixed successfully")
                return True
            print(f"   ❌ Failed to fix imports: {result.stderr}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Auto-fix failed: {e}")
            return False

    def save_report(self, report: str, filepath: Path):
        """Save the analysis report to file."""
        filepath.write_text(report)
        print(f"📄 Report saved to: {filepath}")

    def save_json_results(self, filepath: Path):
        """Save raw results as JSON for further processing."""
        filepath.write_text(json.dumps(self.results, indent=2))
        print(f"📊 Raw results saved to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Analyze and optionally fix dead code")
    parser.add_argument("--fix", action="store_true", help="Automatically fix unused imports")
    parser.add_argument("--report-only", action="store_true", help="Generate report only, no fixes")
    parser.add_argument(
        "--output-dir", type=Path, default=".dev/reports", help="Output directory for reports"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    analyzer = DeadCodeAnalyzer(repo_root)

    # Create output directory
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 Starting dead code analysis...")

    # Run analysis
    vulture_results = analyzer.run_vulture_analysis()
    autoflake_results = analyzer.run_autoflake_analysis()

    # Generate and save report
    report = analyzer.generate_report()
    report_file = output_dir / f"dead_code_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    analyzer.save_report(report, report_file)

    # Save raw JSON results
    json_file = output_dir / f"dead_code_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    analyzer.save_json_results(json_file)

    # Auto-fix if requested
    if args.fix and not args.report_only:
        if analyzer.auto_fix_imports():
            print("🎉 Unused imports have been automatically fixed!")
            print("⚠️  Please review changes and run tests to ensure nothing is broken.")
        else:
            print("❌ Auto-fix failed. Please review the report and fix manually.")

    # Summary
    total_issues = len(vulture_results) + sum(len(files) for files in autoflake_results.values())

    print("\n📊 Analysis Complete!")
    print(f"   Total issues found: {total_issues}")
    print(f"   Report: {report_file}")
    print(f"   Raw data: {json_file}")

    if total_issues > 0:
        print("\n🔧 To fix unused imports automatically:")
        print(f"   python {__file__} --fix")

        print("\n📋 Next steps:")
        print("   1. Review the generated report")
        print("   2. Fix critical issues first")
        print("   3. Add automation to prevent future issues")

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
