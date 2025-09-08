#!/usr/bin/env python3
"""
Simple and safe line length fixer.
Only handles the safest patterns to avoid syntax errors.
"""

import subprocess


def get_e501_files():
    """Get files with E501 errors."""
    result = subprocess.run([
        "uv", "run", "flake8", "src/", "--select=E501"
    ], capture_output=True, text=True)
    
    files = {}
    for line in result.stdout.strip().split('\n'):
        if line and 'E501' in line:
            parts = line.split(':')
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = int(parts[1])
                if file_path not in files:
                    files[file_path] = []
                files[file_path].append(line_num)
    
    return files


def fix_import_lines():
    """Fix long import statements using sed."""
    print("Fixing long import statements...")
    
    files = get_e501_files()
    for file_path in files.keys():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for long from imports
            lines = content.split('\n')
            modified = False
            
            for i, line in enumerate(lines):
                if (line.strip().startswith('from ') and 
                    ' import ' in line and 
                    len(line) > 88 and 
                    ',' in line):
                    
                    # Split the import
                    if ' import ' in line:
                        from_part, import_part = line.split(' import ', 1)
                        if ',' in import_part:
                            imports = [imp.strip() for imp in import_part.split(',')]
                            if len(imports) > 1:
                                indent = len(line) - len(line.lstrip())
                                base_indent = ' ' * indent
                                
                                new_line = f"{base_indent}{from_part} import (\n"
                                for j, imp in enumerate(imports):
                                    comma = ',' if j < len(imports) - 1 else ''
                                    new_line += f"{base_indent}    {imp}{comma}\n"
                                new_line += f"{base_indent})"
                                
                                lines[i] = new_line
                                modified = True
                                print(f"  Fixed import in {file_path}:{i+1}")
            
            if modified:
                with open(file_path, 'w') as f:
                    f.write('\n'.join(lines))
                    
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")


def fix_long_strings():
    """Fix long string literals."""
    print("Fixing long string literals...")
    
    files = get_e501_files()
    for file_path in files.keys():
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            modified = False
            for i, line in enumerate(lines):
                if len(line.rstrip()) > 88 and '"' in line:
                    # Simple string breaking
                    stripped = line.strip()
                    indent = len(line) - len(line.lstrip())
                    base_indent = ' ' * indent
                    
                    # Find long strings
                    import re
                    string_matches = re.findall(r'"([^"]{50,})"', stripped)
                    for match in string_matches:
                        if len(match) > 40:
                            # Find a good break point
                            words = match.split()
                            if len(words) >= 4:
                                mid = len(words) // 2
                                first_part = ' '.join(words[:mid])
                                second_part = ' '.join(words[mid:])
                                
                                new_string = f'"{first_part}" \\\n{base_indent}    "{second_part}"'
                                lines[i] = stripped.replace(f'"{match}"', new_string) + '\n'
                                lines[i] = base_indent + lines[i].lstrip()
                                modified = True
                                print(f"  Fixed string in {file_path}:{i+1}")
                                break
            
            if modified:
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                    
        except Exception as e:
            print(f"Error fixing strings in {file_path}: {e}")


def main():
    """Main function."""
    print("=== Safe Line Length Fixer ===")
    
    # Get initial count
    initial_files = get_e501_files()
    initial_count = sum(len(lines) for lines in initial_files.values())
    print(f"Initial E501 errors: {initial_count}")
    
    # Apply safe fixes
    fix_import_lines()
    fix_long_strings()
    
    # Get final count
    final_files = get_e501_files()
    final_count = sum(len(lines) for lines in final_files.values())
    
    print("\nResults:")
    print(f"  Before: {initial_count} errors")
    print(f"  After:  {final_count} errors")
    print(f"  Fixed:  {initial_count - final_count} errors")
    
    if final_count > 0:
        print("\nRemaining files with issues:")
        for file_path, line_nums in final_files.items():
            print(f"  {file_path}: {len(line_nums)} lines")


if __name__ == "__main__":
    main()
