#!/usr/bin/env python3
"""
Bulk line length fixer using parallel processing and advanced patterns.
This handles the remaining E501 errors efficiently.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor


def get_line_content(file_path: str, line_num: int) -> str:
    """Get the content of a specific line from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if 1 <= line_num <= len(lines):
                return lines[line_num - 1]
    except Exception:
        pass
    return ""


def fix_long_line_advanced(line: str, max_length: int = 88) -> str:
    """Advanced line fixing with multiple strategies."""
    if len(line.rstrip()) <= max_length:
        return line
    
    indent = len(line) - len(line.lstrip())
    base_indent = ' ' * indent
    extra_indent = ' ' * (indent + 4)
    stripped = line.strip()
    
    # Strategy 1: Long string literals
    if '"' in stripped and len(stripped) > max_length:
        # Break long strings at word boundaries
        string_match = re.search(r'"([^"]*)"', stripped)
        if string_match:
            full_string = string_match.group(1)
            if len(full_string) > 40:  # Worth breaking
                # Find a good break point
                words = full_string.split()
                if len(words) > 3:
                    mid = len(words) // 2
                    first_part = ' '.join(words[:mid])
                    second_part = ' '.join(words[mid:])
                    new_line = stripped.replace(
                        f'"{full_string}"',
                        f'"{first_part}" \\\n{extra_indent}"{second_part}"'
                    )
                    return f"{base_indent}{new_line}\n"
    
    # Strategy 2: Function calls with many parameters
    if '(' in stripped and ')' in stripped and ',' in stripped:
        # Count parameters
        paren_content = re.search(r'\(([^)]*)\)', stripped)
        if paren_content:
            params = paren_content.group(1)
            if params.count(',') >= 2:  # Multiple parameters
                func_name = stripped[:stripped.find('(')]
                param_list = [p.strip() for p in params.split(',')]
                
                result = f"{base_indent}{func_name}(\n"
                for i, param in enumerate(param_list):
                    comma = ',' if i < len(param_list) - 1 else ''
                    result += f"{extra_indent}{param}{comma}\n"
                result += f"{base_indent})\n"
                
                # Check if this would actually be better
                if all(len(f"{extra_indent}{p}") <= max_length for p in param_list):
                    return result
    
    # Strategy 3: Dictionary/list literals
    if ('{' in stripped or '[' in stripped) and (',' in stripped):
        # Break dictionary or list items
        for open_char, close_char in [('dict(', ')'), ('{', '}'), ('[', ']')]:
            if open_char in stripped and close_char in stripped:
                start_idx = stripped.find(open_char)
                end_idx = stripped.rfind(close_char)
                if start_idx < end_idx:
                    prefix = stripped[:start_idx + len(open_char)]
                    content = stripped[start_idx + len(open_char):end_idx]
                    suffix = stripped[end_idx:]
                    
                    if ',' in content:
                        items = [item.strip() for item in content.split(',')]
                        if len(items) > 1:
                            result = f"{base_indent}{prefix}\n"
                            for i, item in enumerate(items):
                                if item:  # Skip empty items
                                    comma = ',' if i < len(items) - 1 else ''
                                    result += f"{extra_indent}{item}{comma}\n"
                            result += f"{base_indent}{suffix}\n"
                            return result
    
    # Strategy 4: Long expressions with operators
    operators = [' and ', ' or ', ' + ', ' - ', ' * ', ' == ', ' != ', ' >= ', ' <= ']
    for op in operators:
        if op in stripped:
            parts = stripped.split(op, 1)
            if len(parts) == 2 and len(parts[0]) > 20 and len(parts[1]) > 10:
                result = f"{base_indent}{parts[0]} {op.strip()} \\\n"
                result += f"{extra_indent}{parts[1]}\n"
                return result
    
    # Strategy 5: Simple line break at natural boundaries
    break_chars = [', ', ' = ', ' + ', ' and ', ' or ']
    for char in break_chars:
        if char in stripped:
            # Find the best break point
            pos = stripped.rfind(char, 0, max_length - indent)
            if pos > max_length // 2:  # Don't break too early
                first_part = stripped[:pos + len(char.rstrip())]
                second_part = stripped[pos + len(char):].lstrip()
                result = f"{base_indent}{first_part} \\\n"
                result += f"{extra_indent}{second_part}\n"
                return result
    
    return line  # Return original if no pattern matched


def fix_file_bulk(file_path: str, line_numbers: List[int]) -> int:
    """Fix multiple lines in a file at once."""
    try:
        path = Path(file_path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_count = 0
        # Sort in reverse to maintain line numbers
        for line_num in sorted(line_numbers, reverse=True):
            if 1 <= line_num <= len(lines):
                original = lines[line_num - 1]
                fixed = fix_long_line_advanced(original)
                
                if fixed != original:
                    if '\n' in fixed and fixed.count('\n') > 1:
                        # Multi-line replacement
                        new_lines = fixed.split('\n')[:-1]  # Remove empty last
                        new_lines = [line + '\n' for line in new_lines]
                        lines[line_num - 1:line_num] = new_lines
                    else:
                        lines[line_num - 1] = fixed
                    fixed_count += 1
        
        if fixed_count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✅ Fixed {fixed_count} lines in {file_path}")
        
        return fixed_count
    
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return 0


def main():
    """Main function with parallel processing."""
    print("Getting E501 errors...")
    
    try:
        result = subprocess.run(
            ["uv", "run", "flake8", "src/", "--select=E501"],
            capture_output=True, text=True
        )
        
        # Parse errors
        file_errors: Dict[str, List[int]] = {}
        for line in result.stdout.strip().split('\n'):
            if line and 'E501' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    if file_path not in file_errors:
                        file_errors[file_path] = []
                    file_errors[file_path].append(line_num)
        
        total_errors = sum(len(lines) for lines in file_errors.values())
        print(f"Found {total_errors} E501 errors in {len(file_errors)} files")
        
        if not file_errors:
            print("No E501 errors found!")
            return
        
        # Process files in parallel
        total_fixed = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for file_path, line_numbers in file_errors.items():
                future = executor.submit(fix_file_bulk, file_path, line_numbers)
                futures.append(future)
            
            for future in futures:
                total_fixed += future.result()
        
        print(f"\n🎉 Fixed {total_fixed} out of {total_errors} lines")
        
        # Check remaining
        result_after = subprocess.run(
            ["uv", "run", "flake8", "src/", "--select=E501", "--count"],
            capture_output=True, text=True
        )
        
        remaining = len([line for line in result_after.stdout.split('\n') if 'E501' in line])
        print(f"Remaining E501 errors: {remaining}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
