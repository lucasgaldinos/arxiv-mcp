#!/usr/bin/env python3
"""
Markdown Quality Validation Script for ArXiv MCP Server

This script analyzes converted markdown files and provides quality scores
based on various academic document quality metrics.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any
import argparse
import json

class MarkdownQualityAnalyzer:
    """Analyzes the quality of converted markdown files."""
    
    def __init__(self):
        self.quality_metrics = {
            'yaml_frontmatter': 0.15,
            'heading_structure': 0.20,
            'table_of_contents': 0.10,
            'figure_references': 0.15,
            'mathematical_formulas': 0.15,
            'citation_format': 0.10,
            'content_organization': 0.10,
            'text_quality': 0.05
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single markdown file for quality metrics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            scores = {}
            scores['yaml_frontmatter'] = self._check_yaml_frontmatter(content)
            scores['heading_structure'] = self._check_heading_structure(content)
            scores['table_of_contents'] = self._check_table_of_contents(content)
            scores['figure_references'] = self._check_figure_references(content)
            scores['mathematical_formulas'] = self._check_mathematical_formulas(content)
            scores['citation_format'] = self._check_citation_format(content)
            scores['content_organization'] = self._check_content_organization(content)
            scores['text_quality'] = self._check_text_quality(content)
            
            # Calculate weighted overall score
            overall_score = sum(
                scores[metric] * weight 
                for metric, weight in self.quality_metrics.items()
            )
            
            return {
                'file': str(file_path),
                'overall_score': round(overall_score, 3),
                'metrics': scores,
                'issues': self._identify_issues(content, scores)
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'overall_score': 0.0
            }
    
    def _check_yaml_frontmatter(self, content: str) -> float:
        """Check YAML frontmatter quality."""
        if not content.strip().startswith('---'):
            return 0.0
        
        try:
            parts = content.split('---', 2)
            if len(parts) < 3:
                return 0.2  # Has YAML markers but incomplete
            
            yaml_section = parts[1].strip()
            yaml_data = yaml.safe_load(yaml_section)
            
            if not yaml_data:
                return 0.3
            
            score = 0.5  # Base score for valid YAML
            
            # Check for essential fields
            if 'title' in yaml_data and yaml_data['title']:
                score += 0.2
            if 'authors' in yaml_data and yaml_data['authors']:
                score += 0.1
            if 'arxiv_id' in yaml_data:
                score += 0.1
            if 'processed_at' in yaml_data:
                score += 0.05
            if 'source' in yaml_data:
                score += 0.05
            
            return min(score, 1.0)
            
        except yaml.YAMLError:
            return 0.1  # Malformed YAML
    
    def _check_heading_structure(self, content: str) -> float:
        """Check heading structure and hierarchy."""
        lines = content.split('\n')
        headings = []
        
        for line in lines:
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                headings.append(level)
        
        if not headings:
            return 0.0
        
        score = 0.3  # Base score for having headings
        
        # Check for proper hierarchy
        if len(headings) >= 3:
            score += 0.2
        
        # Check for consistent structure
        has_level_1 = 1 in headings
        has_level_2 = 2 in headings
        
        if has_level_1:
            score += 0.2
        if has_level_2:
            score += 0.2
        
        # Penalize for skipping levels
        max_level = max(headings)
        expected_levels = set(range(1, max_level + 1))
        actual_levels = set(headings)
        
        if expected_levels == actual_levels:
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_table_of_contents(self, content: str) -> float:
        """Check for table of contents."""
        toc_patterns = [
            r'##\s*Table of Contents',
            r'##\s*Contents',
            r'##\s*TOC',
            r'-\s*\[.*\]\(#.*\)'  # Link pattern
        ]
        
        for pattern in toc_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Check if it has actual links
                if re.search(r'-\s*\[.*\]\(#.*\)', content):
                    return 1.0
                else:
                    return 0.5
        
        return 0.0
    
    def _check_figure_references(self, content: str) -> float:
        """Check figure reference quality."""
        # Look for malformed references
        malformed_patterns = [
            r'\[\\\[.*\\\]\]',  # Escaped brackets
            r'\{reference-type=',  # Pandoc artifacts
            r'Fig\.\[\[',  # Complex malformed refs
        ]
        
        malformed_count = 0
        for pattern in malformed_patterns:
            malformed_count += len(re.findall(pattern, content))
        
        # Look for proper figure references
        good_patterns = [
            r'Figure\s+\d+',
            r'Fig\.\s+\d+',
            r'!\[.*\]\(.*\)',  # Image syntax
        ]
        
        good_count = 0
        for pattern in good_patterns:
            good_count += len(re.findall(pattern, content))
        
        if good_count == 0 and malformed_count == 0:
            return 0.7  # No figures, neutral score
        
        if malformed_count > 0:
            score = max(0.0, 1.0 - (malformed_count * 0.2))
        else:
            score = 1.0
        
        if good_count > 0:
            score = min(score + 0.2, 1.0)
        
        return score
    
    def _check_mathematical_formulas(self, content: str) -> float:
        """Check mathematical formula formatting."""
        # Count inline math
        inline_math = len(re.findall(r'\$[^$]+\$', content))
        
        # Count display math
        display_math = len(re.findall(r'\$\$[^$]+\$\$', content))
        
        # Look for LaTeX math artifacts
        artifacts = [
            r'\\begin\{equation\}',
            r'\\end\{equation\}',
            r'\\displaystyle',
        ]
        
        artifact_count = 0
        for pattern in artifacts:
            artifact_count += len(re.findall(pattern, content))
        
        if inline_math == 0 and display_math == 0:
            return 0.8  # No math formulas, neutral score
        
        total_math = inline_math + display_math
        
        if artifact_count > 0:
            score = max(0.0, 1.0 - (artifact_count / total_math * 0.5))
        else:
            score = 1.0
        
        return score
    
    def _check_citation_format(self, content: str) -> float:
        """Check citation formatting."""
        # Count properly formatted citations
        good_citations = len(re.findall(r'@\w+|\[@[\w,\s]+\]', content))
        
        # Count malformed citations
        bad_citations = len(re.findall(r'\\cite\{|\\citep\{', content))
        
        if good_citations == 0 and bad_citations == 0:
            return 0.8  # No citations, neutral score
        
        total_citations = good_citations + bad_citations
        
        if total_citations == 0:
            return 0.8
        
        return good_citations / total_citations
    
    def _check_content_organization(self, content: str) -> float:
        """Check overall content organization."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(lines) < 10:
            return 0.3  # Too short to evaluate
        
        score = 0.5  # Base score
        
        # Check for reasonable paragraph lengths
        paragraphs = content.split('\n\n')
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
        
        if 30 <= avg_paragraph_length <= 200:
            score += 0.2
        
        # Check for proper spacing
        excessive_spacing = len(re.findall(r'\n{4,}', content))
        if excessive_spacing == 0:
            score += 0.2
        
        # Check for bullet points or lists
        if re.search(r'^\s*[-*]\s+', content, re.MULTILINE):
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_text_quality(self, content: str) -> float:
        """Check basic text quality issues."""
        score = 1.0
        
        # Check for excessive whitespace
        if re.search(r'\s{5,}', content):
            score -= 0.2
        
        # Check for HTML artifacts
        html_artifacts = len(re.findall(r'<[^>]+>', content))
        if html_artifacts > 0:
            score -= min(0.3, html_artifacts * 0.05)
        
        # Check for LaTeX artifacts
        latex_artifacts = len(re.findall(r'\\[a-zA-Z]+\{', content))
        if latex_artifacts > 0:
            score -= min(0.3, latex_artifacts * 0.02)
        
        return max(score, 0.0)
    
    def _identify_issues(self, content: str, scores: Dict[str, float]) -> List[str]:
        """Identify specific quality issues."""
        issues = []
        
        if scores['yaml_frontmatter'] < 0.7:
            issues.append("YAML frontmatter missing or incomplete")
        
        if scores['heading_structure'] < 0.6:
            issues.append("Poor heading structure or hierarchy")
        
        if scores['table_of_contents'] < 0.5:
            issues.append("Missing table of contents")
        
        if scores['figure_references'] < 0.7:
            issues.append("Malformed figure references detected")
        
        if scores['mathematical_formulas'] < 0.7:
            issues.append("Mathematical formula formatting issues")
        
        if scores['citation_format'] < 0.7:
            issues.append("Citation formatting problems")
        
        if scores['content_organization'] < 0.6:
            issues.append("Content organization issues")
        
        if scores['text_quality'] < 0.8:
            issues.append("Text quality issues (artifacts, formatting)")
        
        return issues


def main():
    parser = argparse.ArgumentParser(description='Validate markdown quality for ArXiv papers')
    parser.add_argument('path', help='Path to markdown file or directory')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    parser.add_argument('--threshold', '-t', type=float, default=0.8, 
                       help='Quality threshold (default: 0.8)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = MarkdownQualityAnalyzer()
    results = []
    
    path = Path(args.path)
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.glob('**/*.md'))
    else:
        print(f"Error: {path} is not a valid file or directory")
        return 1
    
    print(f"Analyzing {len(files)} markdown files...")
    
    for file_path in files:
        result = analyzer.analyze_file(file_path)
        results.append(result)
        
        if args.verbose or result['overall_score'] < args.threshold:
            print(f"\n📄 {file_path.name}")
            print(f"   Overall Score: {result['overall_score']:.3f}")
            
            if 'metrics' in result:
                print("   Metrics:")
                for metric, score in result['metrics'].items():
                    print(f"     {metric}: {score:.3f}")
            
            if 'issues' in result and result['issues']:
                print("   Issues:")
                for issue in result['issues']:
                    print(f"     ⚠️  {issue}")
    
    # Summary
    total_files = len(results)
    passing_files = len([r for r in results if r['overall_score'] >= args.threshold])
    avg_score = sum(r['overall_score'] for r in results) / total_files
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {total_files}")
    print(f"   Passing threshold ({args.threshold}): {passing_files}")
    print(f"   Average score: {avg_score:.3f}")
    print(f"   Pass rate: {passing_files/total_files*100:.1f}%")
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'summary': {
                    'total_files': total_files,
                    'passing_files': passing_files,
                    'average_score': avg_score,
                    'pass_rate': passing_files/total_files,
                    'threshold': args.threshold
                },
                'results': results
            }, f, indent=2)
        print(f"   Results saved to: {args.output}")
    
    return 0 if passing_files == total_files else 1


if __name__ == '__main__':
    exit(main())