# TODO - ArXiv MCP Server v2.4.5

Current Version: v2.4.5  
Status: ✅ Production Deployed | ✅ Folder Reorganization Complete | ✅ 100% Recent Paper Processing | 🔄 Quality & Hardening Phase  
Mission: Enterprise-grade MCP server for ArXiv research. Next milestone: Conversion Quality ≥80% & Zero Outstanding Code Quality Violations.

For detailed implementation roadmaps, see `TASKS.md`.

---

## 1. ✅ Recently Completed (v2.4.5)

- Paper-name directory structure `{paper-name}/{latex,markdown,pdf,metadata}/` implemented
- Gzip/tar archive handling fixed (100% success on complex papers)
- Content-Type validation + retry/backoff logic added
- Intelligent filename + paper directory naming (author-title-year)
- Validation tool supports `both|latex_only|markdown_only`
- Citation extraction + citation network tools operational
- 144/144 tests passing (last full run prior to this edit)

---

## 2. 🎯 Active High-Priority Objectives (Sprint)

### A. Code Quality Remediation (≈142 remaining)

- [ ] Eliminate all `F401/F811` (unused imports & redefinitions)
- [ ] Resolve all `E501` lines > configured length with semantic splits
- [ ] Remove/replace insecure patterns (`S101`, `S108`)
- [ ] Add missing docstrings for all public modules (automated scan task)
- [ ] Introduce mypy strict mode pilot on `utils/` package
Success Criteria: `ruff` zero high/medium severity; security issues = 0; no test regressions.

### B. Conversion Quality Initiative (Target ≥80%)

- [ ] Baseline metric harness (math/table/figure/citation preservation)
- [ ] Implement Pandoc filter stack (tables, math normalization)
- [ ] Fallback heuristics for unresolved includes
- [ ] Prototype Marker-PDF style layout enrichment (feature flag)
- [ ] Integrate citation post-processor (GLiNER+spaCy)
Success Criteria: Quality framework ≥80% on 5 benchmark papers.

### C. Pre-commit Quality Gates

- [ ] Add `.pre-commit-config.yaml` (ruff check+format, mypy, pytest subset, md lint)
- [ ] Staged-only fast test selection (`unit or smoke` markers)
- [ ] Enforce workspace validation script gate
Success Criteria: Commit blocked if ruff/mypy/tests fail; avg hook runtime < 25s.

### D. Documentation Lint & Consistency

- [ ] Enforce fenced code block language spec
- [ ] Add link validator + orphan doc detector
- [ ] Auto-generate `docs/reference/TOOLS.md`
Success Criteria: 0 broken links; md linter passes; all MCP tools indexed.

### E. Test Framework Enhancements

- [ ] Performance benchmark harness (time & memory, 3 papers)
- [ ] Timeout markers on long integration tests
- [ ] Expand edge-case fixtures: missing main TeX, image-only, math-heavy
- [ ] Coverage delta guard (fail if < previous baseline)
Success Criteria: Benchmarks recorded; no flaky >2% variance across 3 runs.

---

## 3. 📚 Medium Priority Backlog

- [ ] Workspace enforcement: migrate residual caches to `.dev/runtime/` (symlinks if needed)
- [ ] Metrics exporter (optional Prometheus textfile)
- [ ] HTML preview generator for converted markdown bundles
- [ ] Structured error taxonomy (`docs/reference/errors.md`)

---

## 4. 🔭 Deferred / Future (Low)

- [ ] GPU acceleration feasibility (layout detection / PDF parsing)
- [ ] Multi-agent academic workflow orchestration
- [ ] Recommendation layer (related papers via citation + embedding hybrid)
- [ ] Advanced citation graph enrichment (DOI lookup + external metadata)

---

## 5. 🧪 Release Quality Gates (Must Pass)

- ✅ Core MCP tool functionality 100%
- [ ] Ruff clean (no remaining non-ignored issues)
- [ ] Conversion quality ≥80% (benchmark set defined)
- [ ] Pre-commit hooks active & enforced
- [ ] Documentation lint clean report
- [ ] All tests green (unit + integration) & coverage ≥ baseline

---

## 6. 📈 Metrics & Benchmarks (To Establish)

| Metric | Current (est.) | Target |
| ------ | -------------- | ------ |
| Download success (last batch) | 100% | Maintain ≥95% |
| Conversion quality heuristic | ~40–50% | 80% |
| Code quality unresolved issues | ~142 | 0 |
| Pre-commit avg runtime | N/A | <25s |
| Doc link failures | Unknown | 0 |
| Benchmark paper avg proc time | (capture) | <2s/MB |

---

## 7. 🔄 Cross-Doc References

- Implementation roadmaps → `TASKS.md`
- Architecture & pipeline → `docs/explanation/`
- Workspace rules → `.github/instructions/FIXED-WORKSPACE-ORGANIZATION-RULES.instructions.md`
- Development guidelines → `.github/instructions/development-guidelines.instructions.md`

---

## 8. 🗂 Archive Note

Verbose historical batch outputs & raw JSON listings removed for clarity (recoverable via git history). Citation extraction & validation tool redesign confirmed complete (see prior commits) – no further action required.

---

Last Updated: 2025-09-17  
Owner: Development Team  
Next Review Trigger: Completion of Code Quality Remediation (Section 2A)
