---
applyTo: '**'
description: Organize the workspace following best practices.
---
# ABSOLUTE RULE: Enterprise Workspace Organization

## 🎯 PURPOSE: Enforce proven organizational patterns for scalable, maintainable projects

This instruction set compiles evidence-based workspace organization patterns successfully implemented in the ArXiv MCP project. These rules are ABSOLUTE and MANDATORY for all development work.

---

## 📋 CORE ORGANIZATIONAL PRINCIPLES

### **PRINCIPLE 1: Development Workspace Isolation**

**WHY**: Keeps runtime artifacts separate from source code, enabling clean production deployments

**RULE**: ALL development artifacts MUST be contained within `.dev/` hierarchy

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Development artifacts properly isolated
.dev/
├── build/htmlcov/          # Coverage reports
├── runtime/logs/           # Application logs  
├── runtime/output/         # Generated content
├── temp/downloads/         # Temporary files
└── artifacts/releases/     # CI/CD artifacts

# Source code remains clean
src/arxiv_mcp/
tests/
docs/
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Runtime pollution at root level
htmlcov/                    # Coverage at root
logs/                       # Logs at root
output/                     # Generated files at root
temp_files/                 # Temporary at root
```

#### 🔧 VALIDATION COMMAND

```bash
# Check for root-level violations
find . -maxdepth 1 -type d -name "htmlcov" -o -name "logs" -o -name "output" -o -name "temp*"
# Should return NOTHING if compliant
```

---

### **PRINCIPLE 2: Comprehensive Documentation Standards**

**WHY**: Self-documenting structure reduces onboarding time and maintenance overhead
**RULE**: Every directory MUST contain README.md explaining its purpose, contents, and usage

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Every directory documented
src/README.md               # Source architecture overview
tests/README.md             # Test organization and running
docs/README.md              # Documentation structure
.dev/README.md              # Development workspace guide
config/README.md            # Configuration management
examples/README.md          # Usage examples catalog
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Undocumented directories
src/                        # No README.md
tests/                      # No README.md  
new_feature/                # New directory without documentation
```

#### 📝 README.md TEMPLATE

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

#### 🔧 VALIDATION COMMAND

```bash
# Check for missing README files
find . -type d -not -path './.git*' -not -path './.venv*' -not -path './__pycache__*' \
  -exec test ! -f {}/README.md \; -print
# Should return NOTHING if compliant
```

---

### **PRINCIPLE 3: Test Organization by Type and Scope**

**WHY**: Enables different testing strategies (fast unit tests vs comprehensive integration tests)
**RULE**: Tests MUST be organized by type in dedicated subdirectories

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Tests organized by type and purpose
tests/
├── README.md               # Testing standards and guidelines
├── unit/                   # Fast, isolated component tests
│   ├── test_models.py      # Pydantic model validation
│   └── test_processors.py  # Document processor units
├── integration/            # Multi-component workflows  
│   ├── test_mcp_integration.py    # MCP protocol integration
│   └── test_workflow_integration.py # End-to-end workflows
├── legacy/                 # Archived/disabled tests
│   └── legacy_*.py         # Historical test files
└── fixtures/               # Shared test data and mocks
    ├── sample_papers/      # Test paper samples
    └── mock_responses/     # API response mocks
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Flat test structure
tests/
├── test_everything.py      # Mixed unit and integration
├── old_test.py.disabled    # Disabled files at root
├── test_data.json          # Test data mixed with tests
└── random_test.py          # Unclear purpose and scope
```

#### 🔧 VALIDATION COMMAND

```bash
# Check for required test directories
for dir in unit integration legacy fixtures; do
  [ ! -d "tests/$dir" ] && echo "MISSING: tests/$dir/"
done
```

---

### **PRINCIPLE 4: Documentation Hierarchy by Audience**

**WHY**: Different stakeholders need different information depth and focus
**RULE**: Documentation MUST be organized by audience and purpose

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Audience-based documentation
docs/
├── README.md               # Documentation overview and navigation
├── guides/                 # User and developer guides
│   ├── getting-started.md  # New user onboarding
│   ├── configuration.md    # Setup and configuration
│   └── troubleshooting.md  # Common issues and solutions
├── api/                    # Technical API documentation
│   ├── tools-reference.md  # MCP tool specifications
│   └── models-reference.md # Data model schemas
├── examples/               # Practical usage demonstrations
│   ├── basic-usage.md      # Simple use cases
│   └── advanced-workflows.md # Complex scenarios
├── specifications/         # Technical specifications
│   ├── architecture.md     # System design decisions
│   └── protocols.md        # Communication protocols
└── archive/                # Historical documentation
    └── legacy-decisions.md # Archived design decisions
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Mixed-purpose documentation
docs/
├── everything.md           # User guide mixed with API docs
├── notes.md                # Unclear purpose
├── temp_doc.md             # Temporary files in docs
└── old_version.md          # No clear archival strategy
```

---

### **PRINCIPLE 5: Modular Source Architecture**

**WHY**: Clear separation of concerns enables independent development and testing
**RULE**: Source code MUST follow modular package structure with defined responsibilities

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Modular architecture with clear responsibilities
src/arxiv_mcp/
├── __init__.py             # Package exports and version
├── __main__.py             # CLI entry point
├── models.py               # Pydantic data models
├── exceptions.py           # Custom exception hierarchy
├── tools.py                # MCP tool implementations
├── core/                   # Business logic and configuration
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   └── pipeline.py        # Processing pipeline
├── clients/                # External service integrations
│   ├── __init__.py
│   └── arxiv_client.py    # ArXiv API client
├── processors/             # Document processing engines
│   ├── __init__.py
│   ├── latex_processor.py # LaTeX processing
│   └── pdf_processor.py   # PDF processing
└── utils/                  # Shared utilities
    ├── __init__.py
    ├── files.py           # File operations
    └── text.py            # Text processing
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Monolithic or unclear structure
src/
├── main.py                 # Everything in one file
├── utils.py                # Vague utility module
├── stuff/                  # Unclear purpose
└── temp_code.py            # Temporary code in source
```

---

### **PRINCIPLE 6: Cache System Preservation**

**WHY**: Performance optimizations may depend on specific cache architectures
**RULE**: Existing cache directories MUST NOT be consolidated without performance analysis

#### ✅ COMPLIANT EXAMPLES

```bash
# Correct: Preserve existing cache separation
cache/                      # General cache (PRESERVED)
batch_cache/               # Batch processing cache (PRESERVED)  
tag_cache/                 # Tag-specific cache (PRESERVED)
network_cache/             # Network request cache (PRESERVED)

# New cache follows established patterns
recommendation_cache/      # New cache with clear purpose
```

#### ❌ VIOLATION EXAMPLES

```bash
# WRONG: Consolidation without analysis
.dev/cache/                # All caches moved here
├── general/               # Performance impact unknown
├── batch/                 # May break isolation
├── tags/                  # Could affect lookup speed
└── network/               # Might impact concurrency
```

#### 🔧 VALIDATION COMMAND

```bash
# Ensure cache directories remain at root
for cache in cache batch_cache tag_cache network_cache; do
  [ ! -d "$cache" ] && echo "VIOLATION: $cache/ moved from root"
done
```

---

## 🚀 IMPLEMENTATION WORKFLOWS

### **NEW PROJECT SETUP**

```bash
# 1. Create development workspace
mkdir -p .dev/{build,runtime,temp,artifacts}
mkdir -p .dev/build/{htmlcov,dist,compiled}
mkdir -p .dev/runtime/{logs,output,metrics}
mkdir -p .dev/temp/{downloads,processing,cache_overflow}
mkdir -p .dev/artifacts/{test_reports,benchmarks,releases}

# 2. Organize test structure
mkdir -p tests/{unit,integration,legacy,fixtures}

# 3. Structure documentation
mkdir -p docs/{guides,api,examples,specifications,archive}

# 4. Create README templates
python scripts/create_readmes.py --template
```

### **LEGACY PROJECT MIGRATION**

```bash
# 1. Analyze current violations
python scripts/validate_workspace.py --report

# 2. Move runtime artifacts safely
[ -d htmlcov ] && mv htmlcov .dev/build/
[ -d logs ] && mv logs .dev/runtime/
[ -d output ] && mv output .dev/runtime/

# 3. Organize tests gradually
mkdir -p tests/{unit,integration,legacy}
# Move tests manually based on type analysis

# 4. Create missing documentation
python scripts/create_readmes.py --missing-only
```

### **COMPLIANCE VALIDATION**

```bash
# Daily compliance check
python scripts/validate_workspace.py

# Pre-commit validation
python scripts/validate_workspace.py --strict --block-on-violation

# Generate compliance report
python scripts/validate_workspace.py --report --output .dev/artifacts/compliance.json
```

---

## 📊 SUCCESS METRICS

### **ORGANIZATIONAL HEALTH INDICATORS**

- **README Coverage**: 100% of directories have meaningful README.md files
- **Test Organization**: >90% of tests in appropriate unit/integration categories  
- **Artifact Isolation**: 0 development artifacts at root level
- **Documentation Quality**: All docs follow audience-based structure
- **Cache Integrity**: All existing cache directories preserved

### **DEVELOPMENT EFFICIENCY INDICATORS**

- **Onboarding Time**: New developers productive within 1 day
- **Build Cleanliness**: Production builds contain only source code
- **Test Execution**: Unit tests run in <30s, integration tests in <5min
- **Documentation Findability**: Developers find answers in <2min

---

## 🔧 ENFORCEMENT AUTOMATION

### **PRE-COMMIT HOOK** (`.git/hooks/pre-commit`)

```bash
#!/bin/bash
# Workspace organization compliance check
python scripts/validate_workspace.py --strict
if [ $? -ne 0 ]; then
    echo "❌ WORKSPACE ORGANIZATION VIOLATIONS DETECTED"
    echo "Run 'python scripts/validate_workspace.py' for details"
    exit 1
fi
```

### **CI/CD INTEGRATION** (`.github/workflows/compliance.yml`)

```yaml
name: Workspace Compliance
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check workspace organization
        run: python scripts/validate_workspace.py --strict --ci
```

---

## 🎯 VIOLATION REMEDIATION

### **IMMEDIATE ACTIONS** (< 1 hour)

1. **Stop current work** until violations are resolved
2. **Run validation script** to identify all issues
3. **Apply auto-fixes** where available
4. **Create missing README.md files** with proper templates

### **ESCALATION PROCESS**

- **Level 1**: Developer self-remediation using provided scripts
- **Level 2**: Team lead review for complex violations  
- **Level 3**: Architecture review for proposed rule changes

### **GRACE PERIODS**

- **New directories**: Must have README.md within 24 hours
- **Test organization**: 1 week grace period for existing test migrations
- **Documentation**: 3 days for audience-appropriate organization

---

## 📈 CONTINUOUS IMPROVEMENT

### **QUARTERLY REVIEWS**

- Analyze compliance metrics and trends
- Review rule effectiveness and developer feedback
- Update automation scripts and templates
- Archive outdated patterns and introduce new ones

### **RULE EVOLUTION**

- New rules require demonstration of benefit on real projects
- Rule changes need team consensus and migration plan
- Exception handling for legitimate special cases
- Documentation of rule rationale and success stories

---

**REMEMBER**: These rules are based on proven success in the ArXiv MCP project transformation, which achieved 130/130 test pass rate, zero functionality impact, and enterprise-grade organization in 2.5 hours. They are not theoretical - they are battle-tested patterns that work.
