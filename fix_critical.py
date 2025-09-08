#!/usr/bin/env python3
"""
Fix bare except statements by replacing them with Exception.
"""

import re
import subprocess


def fix_bare_except():
    """Fix bare except statements."""
    # Get files with E722 errors
    result = subprocess.run([
        "uv", "run", "flake8", "src/", "--select=E722"
    ], capture_output=True, text=True)
    
    for line in result.stdout.strip().split('\n'):
        if line and 'E722' in line:
            parts = line.split(':')
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = int(parts[1])
                
                try:
                    # Read the file
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Fix the bare except
                    if 0 <= line_num - 1 < len(lines):
                        original_line = lines[line_num - 1]
                        if 'except:' in original_line:
                            # Replace bare except with Exception
                            fixed_line = original_line.replace('except:', 'except Exception:')
                            lines[line_num - 1] = fixed_line
                            
                            # Write back
                            with open(file_path, 'w') as f:
                                f.writelines(lines)
                            
                            print(f"Fixed bare except in {file_path}:{line_num}")
                            
                except Exception as e:
                    print(f"Error fixing {file_path}: {e}")


def fix_variable_shadowing():
    """Fix variable shadowing in paper_notifications.py."""
    file_path = "src/arxiv_mcp/utils/paper_notifications.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the shadowing issue and fix it
        # Look for 'for field in' and replace with 'for notification_field in'
        content = re.sub(
            r'for field in',
            'for notification_field in',
            content
        )
        
        # Also replace any usage of 'field' in those loops
        content = re.sub(
            r'(\s+)field\.',
            r'\1notification_field.',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Fixed variable shadowing in {file_path}")
        
    except Exception as e:
        print(f"Error fixing variable shadowing: {e}")


def main():
    """Main function."""
    print("Fixing critical issues...")
    
    fix_bare_except()
    fix_variable_shadowing()
    
    print("Done!")


if __name__ == "__main__":
    main()
