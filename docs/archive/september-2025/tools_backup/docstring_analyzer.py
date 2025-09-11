#!/usr/bin/env python3
"""
Automated Docstring Detection and Generation Tool
Scans Python files for missing docstrings and provides automation capabilities.
"""

import ast
import os
import sys
from typing import List, Dict, Any


def find_missing_docstrings(file_path: str) -> List[Dict[str, Any]]:
    """Find functions and classes missing docstrings."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        print(f"Warning: Could not parse {file_path}")
        return []

    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            # Check if first statement is a docstring
            has_docstring = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )

            if not has_docstring:
                missing.append(
                    {
                        "type": type(node).__name__,
                        "name": node.name,
                        "line": node.lineno,
                        "file": file_path,
                    }
                )
    return missing


def scan_project(base_dir: str = "src") -> List[Dict[str, Any]]:
    """Scan entire project for missing docstrings."""
    python_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    all_missing = []
    for file_path in python_files:
        missing = find_missing_docstrings(file_path)
        all_missing.extend(missing)

    print(
        f"Found {len(all_missing)} missing docstrings across {len(python_files)} Python files:"
    )

    # Group by file
    by_file = {}
    for item in all_missing:
        file = item["file"]
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(item)

    # Display results
    for file, items in sorted(by_file.items()):
        print(f"\n{file}: {len(items)} missing")
        for item in items:
            print(f"  Line {item['line']}: {item['type']} {item['name']}")

    return all_missing


def generate_docstring(node_type: str, name: str) -> str:
    """Generate appropriate docstring based on node type and name."""
    if node_type == "ClassDef":
        return f'"""{name} class for handling related functionality."""'
    elif node_type in ["FunctionDef", "AsyncFunctionDef"]:
        return f'"""{name.replace("_", " ").title()} functionality."""'
    else:
        return f'"""Docstring for {name}."""'


def main():
    """Main execution function."""
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "src"

    missing = scan_project(base_dir)
    print(f"\nTotal missing docstrings: {len(missing)}")

    # Suggest automation approach
    if missing:
        print("\nAutomation Recommendations:")
        print("1. Use autopep8 for line length fixes")
        print("2. Generate docstrings systematically")
        print("3. Update documentation files")
        print("4. Create comprehensive commit")


if __name__ == "__main__":
    main()
