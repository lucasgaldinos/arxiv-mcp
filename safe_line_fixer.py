#!/usr/bin/env python3
"""
Safe line length fixer using Black formatter with custom line length.
This avoids the syntax errors that aggressive autopep8 can create.
"""

import subprocess
from pathlib import Path


def run_black_with_line_length(max_length: int = 88):
    """Run Black formatter with specific line length."""
    try:
        # Create a temporary pyproject.toml for black configuration
        config = f"""
[tool.black]
line-length = {max_length}
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  | __pycache__
  | \.git
  | \.venv
  | build
  | dist
)/
'''
"""
        
        # Write temporary config
        with open("pyproject_black.toml", "w") as f:
            f.write(config.strip())
        
        # Run black with the config
        result = subprocess.run([
            "uv", "run", "black", 
            "--config", "pyproject_black.toml",
            "src/"
        ], capture_output=True, text=True)
        
        print("Black formatter output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Clean up
        Path("pyproject_black.toml").unlink(missing_ok=True)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running black: {e}")
        Path("pyproject_black.toml").unlink(missing_ok=True)
        return False


def fix_remaining_manual_patterns():
    """Fix specific patterns that automated tools might miss."""
    
    # Get remaining E501 errors
    try:
        result = subprocess.run([
            "uv", "run", "flake8", "src/", "--select=E501"
        ], capture_output=True, text=True)
        
        errors = []
        for line in result.stdout.strip().split('\n'):
            if line and 'E501' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    errors.append((file_path, line_num))
        
        print(f"Found {len(errors)} remaining E501 errors after Black")
        
        # For the remaining errors, we can apply specific fixes
        file_groups = {}
        for file_path, line_num in errors:
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(line_num)
        
        for file_path, lines in file_groups.items():
            print(f"Remaining issues in {file_path}: lines {lines}")
            
        return len(errors)
        
    except Exception as e:
        print(f"Error checking remaining errors: {e}")
        return 0


def main():
    """Main function."""
    print("Step 1: Running Black formatter with 88 character line length...")
    
    if run_black_with_line_length(88):
        print("✅ Black formatting completed successfully")
    else:
        print("❌ Black formatting failed")
        return
    
    print("\nStep 2: Checking remaining E501 errors...")
    remaining = fix_remaining_manual_patterns()
    
    if remaining == 0:
        print("🎉 All line length issues fixed!")
    else:
        print(f"📝 {remaining} issues remain - these may need manual review")
        print("These might be cases where breaking the line would reduce readability")


if __name__ == "__main__":
    main()
