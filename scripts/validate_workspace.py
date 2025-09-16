#!/usr/bin/env python3
"""
Workspace Organization Validator
Enforces enterprise workspace organization rules from ABSOLUTE-RULE-WORKSPACE.instruction.md
"""

import os
from pathlib import Path
import sys


class WorkspaceValidator:
    """Validates and enforces workspace organization rules."""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.violations = []
        self.warnings = []

    def validate_cache_organization(self) -> bool:
        """Validate cache directory organization following current .dev/cache/ strategy."""
        print("🔍 Validating cache organization...")

        # According to current strategy: Caches should be in .dev/cache/ with symlinks at root for compatibility
        cache_base = self.workspace_path / ".dev" / "cache"
        
        if not cache_base.exists():
            self.violations.append("CRITICAL: .dev/cache/ directory does not exist")
            return False

        # Expected cache directories in .dev/cache/
        expected_caches = [
            "batch",      # Batch processing cache
            "tag",        # Tag-specific cache  
            "network",    # Network request cache
            "dependency", # Dependency cache
            "notification", # Notification cache
        ]

        all_good = True
        for cache_name in expected_caches:
            cache_path = cache_base / cache_name
            if not cache_path.exists():
                self.warnings.append(f"Cache directory missing: .dev/cache/{cache_name}")
            
            # Check for proper symlink at root (compatibility requirement)
            root_symlink = self.workspace_path / f"{cache_name}_cache"
            if cache_path.exists() and not root_symlink.exists():
                self.warnings.append(f"Missing compatibility symlink: {cache_name}_cache -> .dev/cache/{cache_name}")

        return all_good

    def validate_output_organization(self) -> bool:
        """Validate output directory organization."""
        print("🔍 Validating output organization...")

        # Check for primary output directory (should be symlink to .dev/runtime/output)
        output_dir = self.workspace_path / "output"
        runtime_output = self.workspace_path / ".dev" / "runtime" / "output"
        
        if not output_dir.exists() and not runtime_output.exists():
            self.violations.append("CRITICAL: No output directory found (neither output/ nor .dev/runtime/output/)")
            return False
        
        # Verify proper organization: either direct .dev/runtime/output or symlink
        if output_dir.exists() and output_dir.is_symlink():
            # Good: symlink setup for compatibility
            target = output_dir.resolve()
            if target != runtime_output.resolve():
                self.violations.append(f"VIOLATION: output/ symlink points to wrong location: {target}")
        elif runtime_output.exists():
            # Good: direct .dev/runtime/output setup
            pass
        else:
            self.violations.append("VIOLATION: output/ exists but is not properly organized")

        # Check that the actual output directory has proper structure
        actual_output = runtime_output if runtime_output.exists() else output_dir
        
        # Required subdirectories for ArXiv MCP
        required_subdirs = {"latex", "markdown", "metadata"}
        
        if actual_output.exists():
            existing_subs = {d.name for d in actual_output.iterdir() if d.is_dir()}
            missing_subs = required_subdirs - existing_subs
            if missing_subs:
                self.warnings.append(f"Missing output subdirectories: {missing_subs}")

        # Check for scattered output directories
        scattered_output_patterns = [
            "test_output",
            "arxiv_mcp_test_output", 
            "test_fixed_tools",
            "nonexistent",
            "arxiv-mcp-dev",
        ]

        for pattern in scattered_output_patterns:
            if (self.workspace_path / pattern).exists():
                self.violations.append(f"VIOLATION: Scattered output directory found: {pattern}")

        print(f"✅ Output organization: {len(self.violations) == 0}")
        return len(self.violations) == 0

    def validate_root_cleanliness(self) -> bool:
        """Validate root directory cleanliness."""
        print("🔍 Validating root directory cleanliness...")

        # Prohibited file patterns in root
        prohibited_patterns = [
            "test_*.py",
            "*_test.py",
            "debug_*.py",
            "*_debug.py",
            "tool_*.py",
            "*_tool.py",
            "*.db",
        ]

        root_files = [f for f in self.workspace_path.iterdir() if f.is_file()]

        for file_path in root_files:
            filename = file_path.name

            # Check against prohibited patterns
            for pattern in prohibited_patterns:
                if self._matches_pattern(filename, pattern):
                    self.violations.append(f"VIOLATION: Development file in root: {filename}")

        print(f"✅ Root cleanliness: {len(self.violations) == 0}")
        return len(self.violations) == 0

    def validate_documentation_unity(self) -> bool:
        """Validate single source of truth for documentation."""
        print("🔍 Validating documentation unity...")

        # Check for multiple TODO files
        todo_patterns = ["TODO_MASTER.md", "TODO_FINAL.md", "TODO_MAIN.md", "TASKS.md", "TODO_*.md"]

        for pattern in todo_patterns:
            matches = list(self.workspace_path.glob(pattern))
            if matches:
                for match in matches:
                    if match.name != "TODO.md":  # Allow the main TODO.md
                        self.violations.append(f"VIOLATION: Multiple TODO file: {match.name}")

        # Check TODO.md exists
        todo_path = self.workspace_path / "TODO.md"
        if not todo_path.exists():
            self.violations.append("CRITICAL: TODO.md does not exist")

        print(f"✅ Documentation unity: {len(self.violations) == 0}")
        return len(self.violations) == 0

    def validate_archive_structure(self) -> bool:
        """Validate archive structure if archives exist."""
        print("🔍 Validating archive structure...")

        archive_path = self.workspace_path / "docs" / "archive"
        if not archive_path.exists():
            self.warnings.append("No archive directory found (this is acceptable)")
            return True

        # Check for proper timestamp structure
        for item in archive_path.iterdir():
            if item.is_dir():
                # Should follow YYYY-MM-month pattern
                if not self._is_valid_archive_name(item.name):
                    self.warnings.append(
                        f"Archive directory name doesn't follow pattern: {item.name}"
                    )

        print("✅ Archive structure: valid")
        return True

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names."""
        import fnmatch

        return fnmatch.fnmatch(filename, pattern)

    def _is_valid_archive_name(self, name: str) -> bool:
        """Check if archive directory name follows YYYY-MM-month pattern."""
        import re

        pattern = r"^\d{4}-\d{2}-[a-z]+$"
        return bool(re.match(pattern, name))

    def fix_violations(self) -> bool:
        """Attempt to fix detected violations."""
        print("🔧 Attempting to fix violations...")

        if not self.violations:
            print("✅ No violations to fix")
            return True

        print(f"Found {len(self.violations)} violations:")
        for violation in self.violations:
            print(f"  ❌ {violation}")

        # For now, just report violations
        # Auto-fixing would require more complex logic
        print("⚠️  Auto-fixing not implemented. Manual intervention required.")
        return False

    def generate_report(self) -> dict:
        """Generate comprehensive validation report."""
        return {
            "violations": self.violations,
            "warnings": self.warnings,
            "compliance_score": self._calculate_compliance_score(),
            "is_compliant": len(self.violations) == 0,
        }

    def _calculate_compliance_score(self) -> float:
        """Calculate compliance score (0-100)."""
        violations = len(self.violations)

        if violations == 0:
            return 100.0
        # Penalty per violation
        penalty = min(violations * 20, 100)
        return max(0.0, 100.0 - penalty)

    def run_full_validation(self) -> bool:
        """Run all validation checks."""
        print("🏗️  Running comprehensive workspace validation...")
        print("=" * 60)

        [
            self.validate_cache_organization(),
            self.validate_output_organization(),
            self.validate_root_cleanliness(),
            self.validate_documentation_unity(),
            self.validate_archive_structure(),
        ]

        report = self.generate_report()

        print("=" * 60)
        print("📊 Validation Report:")
        print(f"   Compliance Score: {report['compliance_score']:.1f}/100")
        print(f"   Violations: {len(self.violations)}")
        print(f"   Warnings: {len(self.warnings)}")
        print(f"   Status: {'✅ COMPLIANT' if report['is_compliant'] else '❌ NON-COMPLIANT'}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"    • {warning}")

        if self.violations:
            print("\n❌ Violations:")
            for violation in self.violations:
                print(f"    • {violation}")

        return report["is_compliant"]


def main():
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate workspace organization")
    parser.add_argument("--fix", action="store_true", help="Attempt to automatically fix violations")
    parser.add_argument("workspace_path", nargs="?", default=os.getcwd(), help="Path to workspace to validate")
    
    args = parser.parse_args()
    
    print(f"🔍 Validating workspace: {args.workspace_path}")

    validator = WorkspaceValidator(args.workspace_path)
    is_compliant = validator.run_full_validation()

    if is_compliant:
        print("\n🎉 Workspace is ENTERPRISE COMPLIANT!")
        sys.exit(0)
    else:
        print("\n💥 Workspace has COMPLIANCE VIOLATIONS!")
        print("\nRefer to .github/instructions/FIXED-WORKSPACE-ORGANIZATION-RULES.instructions.md for rules")
        if args.fix:
            print("🔧 Auto-fix functionality not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
