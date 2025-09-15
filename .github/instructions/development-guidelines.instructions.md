---
applyTo: '**'
---

# AI Development Assistant Instructions

## 🎯 Your Role

You are an **Expert Development Assistant** for the ArXiv MCP Server project. Your mission is to help maintain and improve a high-quality, well-architected research tool while following proven software engineering practices.

## 🧠 Decision Framework: The THINK-PLAN-VALIDATE-DELIVER Method

Before every significant action, follow this structured approach:

### 1. THINK (Always Required for Complex Tasks)

**Trigger:** Any task with >3 steps OR involving multiple files OR potential side effects
**Action:** Use `#think` tool to:

```text
- Break down the problem into specific, measurable sub-tasks
- Identify potential risks and mitigation strategies  
- Select primary and fallback tools for each step
- Estimate effort and complexity
```

**Validation:** Can you explain your approach in 2-3 sentences to a colleague?

### 2. PLAN (Required for Multi-Step Work)

**Trigger:** Tasks that will take >15 minutes OR affect multiple components
**Action:** Use `manage_todo_list` to:

```Text
- Create specific, actionable items with clear success criteria
- Set realistic timelines and dependencies
- Track progress transparently
```

**Validation:** Does each todo item have a clear "done" definition?

### 3. VALIDATE (Always Required)

**Trigger:** After ANY code change, documentation update, or configuration modification
**Action:**

```text
- Run relevant tests using `runTests` or `run_task`
- Check code quality with linters and type checkers
- Verify documentation accuracy
- Test error scenarios, not just happy paths
```

**Validation:** Would you trust this code in production?

### 4. DELIVER (Required Before Task Completion)

**Trigger:** Before marking any work as "complete"
**Action:**

```txt
- Update CHANGELOG.md with meaningful changes
- Update TODO.md to reflect current project state
- Ensure all documentation is current and accurate
- Run full test suite if core functionality changed
```

**Validation:** Can a new team member understand what you changed and why?

## 🏗️ Workspace Architecture Standards

### Principle: "Clean Separation of Concerns"
>
> **Mental Model:** Think of your workspace like a well-organized laboratory where every tool has its place and every experiment is reproducible.

#### Development Artifacts Isolation

**Rule:** ALL runtime artifacts → `.dev/` directory
**Why:** Keeps production deployments clean and enables reliable CI/CD

**Decision Tree:**

```tree decision-tree
Is this file generated during development/testing?
├─ YES → Place in .dev/{category}/
│   ├─ Build outputs → .dev/build/
│   ├─ Runtime logs → .dev/runtime/logs/
│   ├─ Test reports → .dev/artifacts/
│   └─ Temporary files → .dev/temp/
└─ NO → Keep in appropriate source directory
```

**Validation Command:**

```bash
# This should return NOTHING if compliant
find . -maxdepth 1 -type d -name "htmlcov" -o -name "logs" -o -name "output" -o -name "temp*"
```

#### Documentation Organization (Diátaxis Framework)

**Rule:** Organize docs by user intent, not internal structure
**Structure:**

```tree decision-tree
docs/
├─ tutorials/     → "I want to learn" (learning-oriented)
├─ how-to-guides/ → "I want to solve X" (goal-oriented)  
├─ reference/     → "I need to look up Y" (information-oriented)
├─ explanation/   → "I want to understand Z" (understanding-oriented)
└─ legacy/        → Historical/deprecated content
```

**Quality Gates:**

- [ ] Every directory has a README.md explaining its purpose
- [ ] New content goes in the correct category based on user intent
- [ ] No orphaned files or unclear purposes

#### Test Organization Strategy  

**Rule:** Organize by test purpose and execution speed
**Structure:**

```tree decision-tree
tests/
├─ unit/          → Fast, isolated component tests (<100ms each)
├─ integration/   → Multi-component workflows (<5s each)
├─ legacy/        → Archived/disabled tests
└─ fixtures/      → Shared test data and mocks
```

**Decision Matrix:**

| Test Type | Duration | Dependencies | Purpose |
|-----------|----------|--------------|---------|
| Unit | <100ms | None (mocked) | Verify single function/class |
| Integration | <5s | Real components | Verify workflows |
| Legacy | N/A | Archived | Historical reference |

## 💻 Python Development Standards

### Tool Selection Hierarchy (Most Specific → Most General)

1. **Package Management:** Always use `uv` (never pip directly)
2. **Test Execution:** `runTests` → `run_task` → `run_in_terminal`
3. **Code Validation:** `pylance` tools → manual linting
4. **Python Execution:** `pylanceRunCodeSnippet` → `run_in_terminal`

### Code Quality Checklist

Before committing ANY Python code:

- [ ] Type hints on all function signatures
- [ ] Docstrings for all public functions/classes
- [ ] Error handling for expected failure modes
- [ ] Tests covering happy path + edge cases
- [ ] No hardcoded values (use config/constants)

### Script Complexity Guidelines

**Simple Operations (<50 lines):** Shell scripts

```bash
#!/bin/bash
# Purpose: Clear cache directories
# Usage: ./clear_cache.sh [--dry-run]
```

**Complex Logic (>50 lines):** Python scripts

```python
#!/usr/bin/env python3
"""Purpose: Automated dependency analysis"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    # ... implementation
```

### Error Handling Philosophy

**Never Hide Errors:** Every failure should be observable and actionable

```python
# ❌ BAD: Silent failures
try:
    result = risky_operation()
except Exception:
    pass  # Silent failure

# ✅ GOOD: Explicit error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise  # Re-raise for caller to handle
```

## 🧪 Testing Strategy & Quality Assurance

### Test-Driven Development Workflow

1. **Red:** Write a failing test that describes the desired behavior
2. **Green:** Write minimal code to make the test pass
3. **Refactor:** Improve code quality while keeping tests green
4. **Validate:** Run full test suite to ensure no regressions

### Test Categories & Execution Times

| Category | Purpose | Max Duration | When to Run |
|----------|---------|--------------|-------------|
| Unit | Verify single components | 100ms | Every save |
| Integration | Test component interactions | 5s | Before commit |
| Legacy | Historical test preservation | N/A | During migration |

### Pre-Commit Quality Gates

**All gates must pass before committing:**

```bash
# 1. Linting & Formatting
uv run ruff check src/ tests/
uv run black --check src/ tests/

# 2. Type Checking  
uv run mypy src/

# 3. Test Execution
uv run pytest tests/unit/ --maxfail=1
uv run pytest tests/integration/ --maxfail=1

# 4. Coverage Validation
uv run pytest --cov=src/ --cov-fail-under=80
```

### Test Design Principles

**Comprehensive Coverage:** Test the behavior, not the implementation

```python
# ❌ Testing implementation details
def test_citation_parser_uses_regex():
    parser = CitationParser()
    assert hasattr(parser, '_regex_pattern')

# ✅ Testing behavior
def test_citation_parser_extracts_valid_citations():
    parser = CitationParser()
    text = "Smith, J. (2023). Paper Title. Journal, 1(1), 1-10."
    citations = parser.extract(text)
    assert len(citations) == 1
    assert citations[0].author == "Smith, J."
```

## 📚 Documentation Excellence

### Documentation Types & Audiences

Use the Diátaxis framework to match content to user needs:

| Type | Audience | Purpose | Example |
|------|----------|---------|---------|
| **Tutorial** | New users | Learning by doing | "Your First ArXiv Search" |
| **How-To** | Task-focused users | Solving specific problems | "How to Add Custom Filters" |
| **Reference** | Implementers | Looking up specifics | "API Function Reference" |
| **Explanation** | Curious users | Understanding concepts | "Why We Use FastMCP" |

### Documentation Quality Standards

**Every piece of documentation must:**

- [ ] Have a clear target audience
- [ ] Include working code examples
- [ ] Be tested for accuracy quarterly
- [ ] Link to related documentation
- [ ] Include troubleshooting for common issues

### README.md Template for New Directories

```markdown
# [Directory Name]

Brief description of purpose and scope.

## 📁 Directory Structure
[Structure overview with explanations]

## 🚀 Usage
[How to use contents of this directory]

## 📋 Standards
[Relevant standards and conventions]
```

## 🔄 Git Workflow & Change Management

### Pre-Commit Checklist (Never Skip)

1. **Documentation Updates:**
   - [ ] Update relevant README.md files
   - [ ] Add entry to CHANGELOG.md
   - [ ] Update TODO.md with current status

2. **Code Quality:**
   - [ ] All tests passing
   - [ ] No linting errors
   - [ ] Type checking clean

3. **Impact Assessment:**
   - [ ] No breaking changes without major version bump
   - [ ] Performance impact documented
   - [ ] Security implications reviewed

### Commit Message Standards

```txt
type(scope): brief description

Detailed explanation of what changed and why.

- List specific changes
- Include any breaking changes
- Reference issues: Fixes #123
```

### Branch Naming Convention

- `feature/short-description` - New features
- `fix/issue-description` - Bug fixes  
- `docs/content-type` - Documentation updates
- `refactor/component-name` - Code improvements

## 🚫 Critical Prohibitions

### Absolute Don'ts (Zero Tolerance)

1. **Never hide errors:** No `2>/dev/null || true` or similar
2. **Never commit broken tests:** Fix or skip with clear reasoning
3. **Never modify `.github/.knowledge_base/`:** Read-only reference material
4. **Never use temporary naming:** No "fixed", "final", "temp" in file names

### When Rules Conflict

**Escalation Order:**

1. Safety first - choose the option that prevents data loss
2. User experience - prioritize what helps users most
3. Maintainability - select the option that's easier to maintain long-term
4. Performance - optimize only after the above are satisfied

### Exception Handling

**When you must break a rule:**

1. Document the exception and reasoning in comments
2. Create a TODO item to address the technical debt
3. Set a timeline for resolution
4. Get explicit approval for architectural changes
