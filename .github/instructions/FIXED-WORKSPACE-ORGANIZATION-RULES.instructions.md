---
applyTo: "**"
priority: "ABSOLUTE"
status: "FIXED-INSTRUCTION"
---

# FIXED WORKSPACE ORGANIZATION RULES

## 🚨 ABSOLUTE RULES - NEVER VIOLATE

These rules are **FIXED INSTRUCTIONS** that must ALWAYS be followed to prevent circular logic and organizational chaos.

### Rule 1: Classification by VALUE, Not Temporality

**NEVER classify files by perceived "temporality" - classify by ACTUAL VALUE and PURPOSE.**

#### ✅ CORRECT Classification System

**`.dev/docs/` - Implementation Documentation**

- **Purpose**: Permanent technical documentation of implementations
- **Contains**: Implementation summaries, analysis reports, technical decisions
- **Examples**: `citation_fixes_summary.md`, `enhanced_mcp_integration_summary.md`
- **Lifecycle**: Permanent - valuable for knowledge transfer and maintenance
- **Value**: HIGH - Essential for understanding system evolution

**`.dev/tests/` - Development Validation**

- **Purpose**: Development-specific testing and validation scripts
- **Contains**: Implementation validation tests, integration tests, performance tests
- **Examples**: `test_enhanced_implementation.py`, `test_mcp_integration.py`
- **Lifecycle**: Maintained alongside features - used for ongoing validation
- **Value**: HIGH - Critical for development workflow and regression prevention

**`.dev/debug/` - Investigation Tools**

- **Purpose**: Debugging and troubleshooting scripts for specific issues
- **Contains**: Component-specific debug scripts, investigation tools
- **Examples**: `debug_citation.py`, `debug_performance.py`, `debug_boundary.py`
- **Lifecycle**: Preserved for regression testing and future issue investigation
- **Value**: MEDIUM-HIGH - Essential for troubleshooting and understanding system behavior

**`.dev/temp/` - True Temporary Artifacts**

- **Purpose**: Files with short lifecycle, automatically generated, no long-term value
- **Contains**: `__pycache__/`, build intermediates, cache overflow, scratch files
- **Examples**: Python bytecode, temporary downloads, processing scratch space
- **Lifecycle**: Automatically cleaned up, safe to delete anytime
- **Value**: NONE - No preservation needed

#### ❌ PROHIBITED Misclassifications

**NEVER put these in `.dev/temp/`:**

- Implementation documentation or summaries
- Validation tests or debugging scripts
- Analysis reports or technical decisions
- Any file that provides ongoing value for development

**NEVER create "temporary" names:**

- No files named with `_temp`, `_final`, `_fixed` suffixes
- No directories like `temp_analysis/` or `scratch_tests/`
- Use proper classification based on actual purpose

### Rule 2: Consistent Environment Management

**ALL Python execution MUST use `uv run` consistently across ALL contexts.**

#### ✅ REQUIRED Patterns

**VS Code Tasks:**

```json
{
  "command": "uv",
  "args": ["run", "python", "-m", "tool_name", "...args"]
}
```text

**Terminal Commands:**

```bash
uv run python script.py
uv run python -m pytest tests/
uv run python -m black src/ tests/
```bash

**Development Scripts:**

```python
#!/usr/bin/env uv run python
# Use uv shebang for development scripts
```text

#### ❌ PROHIBITED Patterns

**NEVER use bare `python` commands:**

- ❌ `python -m pytest`
- ❌ `python script.py`
- ❌ `python -m black`

**NEVER mix environments:**

- ❌ Some tasks use `uv run`, others use `python`
- ❌ Manual commands bypass uv environment
- ❌ CI/CD uses different pattern than local development

### Rule 3: Systematic Organization Enforcement

**ALWAYS follow systematic classification process.**

#### Decision Tree for File Classification

```tree decision-tree
Is this file valuable for future development work?
├─ YES → Classify by primary purpose:
│   ├─ Documents implementation? → .dev/docs/
│   ├─ Tests or validates functionality? → .dev/tests/
│   ├─ Debugs or investigates issues? → .dev/debug/
│   └─ Runtime artifacts or reports? → .dev/artifacts/
└─ NO → Is it automatically generated with no long-term value?
    ├─ YES → .dev/temp/
    └─ NO → Reassess classification (probably has value)
```text

#### Validation Commands

**Check for violations:**

```bash
# Find misplaced valuable files
find .dev/temp/ -name "*.md" -o -name "test_*.py" -o -name "debug_*.py"

# Find bare python commands in tasks
grep -r "\"command\": \"python\"" .vscode/

# Validate organization compliance
uv run python scripts/validate_workspace.py --scan-violations
```bash

### Rule 4: Documentation Standards

**EVERY new `.dev/` subdirectory MUST have a README.md explaining its purpose.**

#### Required README Template

```markdown
# [Directory Name]

## 📁 Purpose

[Clear explanation of what goes in this directory]

## 🔄 Usage

[How to use contents of this directory]

## 📋 Standards

[Relevant standards and conventions]

## 🏗️ Organization Principle

[Why this separation exists and how it fits the overall structure]
```text

## 🔍 ENFORCEMENT MECHANISMS

### Automated Validation

**Pre-commit hooks MUST validate:**

- No valuable files in `.dev/temp/`
- All VS Code tasks use `uv run` pattern
- All `.dev/` subdirectories have README.md files
- No circular classification logic

### Manual Review Checkpoints

**Before any workspace changes:**

1. **Value Assessment**: Does this file provide ongoing value?
2. **Purpose Classification**: What is the primary purpose?
3. **Lifecycle Analysis**: How long should this be preserved?
4. **Environment Consistency**: Does this use proper uv patterns?

### Error Prevention

**Common Anti-Patterns to Avoid:**

- Creating "temp" files that have permanent value
- Mixing environment management approaches
- Classification based on perceived urgency rather than actual value
- Creating exceptions without documented rationale

## 📋 COMPLIANCE VALIDATION

### Daily Development Checklist

- [ ] All new files classified by value, not temporality
- [ ] All Python commands use `uv run` consistently
- [ ] No valuable artifacts in `.dev/temp/`
- [ ] New directories have proper README documentation
- [ ] Environment usage consistent across all tools

### Weekly Audit Requirements

- [ ] Run workspace validation script
- [ ] Check for VS Code task consistency
- [ ] Validate `.dev/` organization compliance
- [ ] Review any new file classifications
- [ ] Update documentation for any changes

## 🚫 VIOLATION CONSEQUENCES

**Immediate Remediation Required:**

- Fix any violations as soon as discovered
- Document the correction in development notes
- Update processes to prevent recurrence
- Review decision-making process for improvements

**Zero Tolerance Items:**

- Valuable development artifacts in `.dev/temp/`
- Bare `python` commands in VS Code tasks
- Missing README files in `.dev/` subdirectories
- Circular or contradictory classification rules

---

## 📝 IMPLEMENTATION HISTORY

**Created**: 2025-09-15
**Reason**: Resolved circular workspace organization logic that was misclassifying valuable development artifacts as "temporary" files
**Validated**: Successful reorganization of citation fixes, enhanced implementation tests, and debug scripts from `.dev/temp/` to proper classification
**Status**: FIXED INSTRUCTION - permanent development standard

This document serves as the definitive reference for workspace organization and MUST be consulted before making any changes to file classification or environment management approaches.
