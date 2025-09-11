#!/usr/bin/env python3
"""
Workspace Organization Validator
Enforces enterprise workspace organization rules from ABSOLUTE-RULE-WORKSPACE.instruction.md
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import sqlite3

class WorkspaceValidator:
    """Validates and enforces workspace organization rules."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.violations = []
        self.warnings = []
        
    def validate_cache_organization(self) -> bool:
        """Validate cache directory organization following PRINCIPLE 6: Cache System Preservation."""
        print("🔍 Validating cache organization...")
        
        # According to PRINCIPLE 6: Existing cache directories MUST be preserved
        # These are COMPLIANT and should remain at root level:
        preserved_cache_dirs = [
            'cache',           # General cache (PRESERVED)
            'batch_cache',     # Batch processing cache (PRESERVED)  
            'tag_cache',       # Tag-specific cache (PRESERVED)
            'network_cache'    # Network request cache (PRESERVED)
        ]
        
        # Validate that preserved caches exist and are not moved
        all_good = True
        for cache_dir in preserved_cache_dirs:
            cache_path = self.workspace_path / cache_dir
            if cache_path.exists():
                # This is GOOD - cache is preserved as required
                continue
            else:
                # Check if it was incorrectly moved to .dev/
                dev_cache_path = self.workspace_path / '.dev' / 'cache' / cache_dir.replace('_cache', '')
                if dev_cache_path.exists():
                    self.violations.append(f"VIOLATION: {cache_dir}/ moved to .dev/ - should remain at root for performance")
                    all_good = False
        
        return all_good
        
        if missing_dirs:
            self.warnings.append(f"Missing cache subdirectories: {missing_dirs}")
            
        print(f"✅ Cache organization: {len(self.violations) == 0}")
        return len(self.violations) == 0
        
    def validate_output_organization(self) -> bool:
        """Validate output directory organization."""
        print("🔍 Validating output organization...")
        
        output_dir = self.workspace_path / 'output'
        if not output_dir.exists():
            self.violations.append("CRITICAL: output/ directory does not exist")
            return False
            
        # Required environment directories
        required_envs = {'test', 'production', 'dev'}
        required_subdirs = {'latex', 'markdown', 'metadata'}
        
        existing_envs = {d.name for d in output_dir.iterdir() if d.is_dir()}
        missing_envs = required_envs - existing_envs
        
        if missing_envs:
            self.violations.append(f"Missing output environments: {missing_envs}")
            
        # Check each environment has required subdirectories
        for env in required_envs:
            env_path = output_dir / env
            if env_path.exists():
                existing_subs = {d.name for d in env_path.iterdir() if d.is_dir()}
                missing_subs = required_subdirs - existing_subs
                if missing_subs:
                    self.warnings.append(f"Missing {env} subdirectories: {missing_subs}")
                    
        # Check for scattered output directories
        scattered_output_patterns = [
            'test_output', 'arxiv_mcp_test_output', 'test_fixed_tools',
            'nonexistent', 'arxiv-mcp-dev'
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
            'test_*.py', '*_test.py', 'debug_*.py', '*_debug.py',
            'tool_*.py', '*_tool.py', '*.db'
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
        todo_patterns = [
            'TODO_MASTER.md', 'TODO_FINAL.md', 'TODO_MAIN.md',
            'TASKS.md', 'TODO_*.md'
        ]
        
        for pattern in todo_patterns:
            matches = list(self.workspace_path.glob(pattern))
            if matches:
                for match in matches:
                    if match.name != 'TODO.md':  # Allow the main TODO.md
                        self.violations.append(f"VIOLATION: Multiple TODO file: {match.name}")
                        
        # Check TODO.md exists
        todo_path = self.workspace_path / 'TODO.md'
        if not todo_path.exists():
            self.violations.append("CRITICAL: TODO.md does not exist")
            
        print(f"✅ Documentation unity: {len(self.violations) == 0}")
        return len(self.violations) == 0
        
    def validate_archive_structure(self) -> bool:
        """Validate archive structure if archives exist."""
        print("🔍 Validating archive structure...")
        
        archive_path = self.workspace_path / 'docs' / 'archive'
        if not archive_path.exists():
            self.warnings.append("No archive directory found (this is acceptable)")
            return True
            
        # Check for proper timestamp structure
        for item in archive_path.iterdir():
            if item.is_dir():
                # Should follow YYYY-MM-month pattern
                if not self._is_valid_archive_name(item.name):
                    self.warnings.append(f"Archive directory name doesn't follow pattern: {item.name}")
                    
        print(f"✅ Archive structure: valid")
        return True
        
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
        
    def _is_valid_archive_name(self, name: str) -> bool:
        """Check if archive directory name follows YYYY-MM-month pattern."""
        import re
        pattern = r'^\d{4}-\d{2}-[a-z]+$'
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
        
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        return {
            'violations': self.violations,
            'warnings': self.warnings,
            'compliance_score': self._calculate_compliance_score(),
            'is_compliant': len(self.violations) == 0
        }
        
    def _calculate_compliance_score(self) -> float:
        """Calculate compliance score (0-100)."""
        total_checks = 5  # Number of validation categories
        violations = len(self.violations)
        
        if violations == 0:
            return 100.0
        else:
            # Penalty per violation
            penalty = min(violations * 20, 100)
            return max(0.0, 100.0 - penalty)
            
    def run_full_validation(self) -> bool:
        """Run all validation checks."""
        print("🏗️  Running comprehensive workspace validation...")
        print("=" * 60)
        
        results = [
            self.validate_cache_organization(),
            self.validate_output_organization(),
            self.validate_root_cleanliness(),
            self.validate_documentation_unity(),
            self.validate_archive_structure()
        ]
        
        report = self.generate_report()
        
        print("=" * 60)
        print(f"📊 Validation Report:")
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
                
        return report['is_compliant']


def main():
    """Main validation entry point."""
    if len(sys.argv) > 1:
        workspace_path = sys.argv[1]
    else:
        workspace_path = os.getcwd()
        
    print(f"🔍 Validating workspace: {workspace_path}")
    
    validator = WorkspaceValidator(workspace_path)
    is_compliant = validator.run_full_validation()
    
    if is_compliant:
        print("\n🎉 Workspace is ENTERPRISE COMPLIANT!")
        sys.exit(0)
    else:
        print("\n💥 Workspace has COMPLIANCE VIOLATIONS!")
        print("\nRefer to .github/instructions/ABSOLUTE-RULE-WORKSPACE.instruction.md for rules")
        sys.exit(1)


if __name__ == "__main__":
    main()
