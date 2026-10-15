# Feature: LaTeX/KaTeX Math Sanitization

## Objective
Sanitize LaTeX/KaTeX math blocks across all Markdown files in the repository to prevent `'_' allowed only in math mode` parse errors and remove redundant `, \,` spacing.

## Problem & Root Cause
1. Markdown engines (CommonMark/GFM) unescape `\_` inside math delimiters to literal `_` before handing the string to math renderers.
2. Inside `\text{...}`, KaTeX operates in text mode where `_` is prohibited unless escaped via LaTeX-specific macros. When it encounters `_`, KaTeX throws `'_' allowed only in math mode`.
3. The combination `, \,` introduces an unnecessary thin space directly after a comma, producing visual anomalies like `, ,`.

## Why
Ensures seamless, robust KaTeX, MathJax, and GitHub math rendering across all documentation, case studies, and specs.

## Scope & Constraints
- Scope: 42 Markdown files across root (`README.md`, `MEDIUM_POST.md`), `docs/`, and `openspec/`.
- Convention: Replace `\text{foo-bar}` and remove redundant `, \,` in math coordinates.
- Constraints: Maintain exact mathematical and architectural meaning; verify 0 regression in tests (`pytest`).

## Tasks
- [x] TASK-1: Sanitize root user-facing documentation (`README.md`, `MEDIUM_POST.md`)
- [x] TASK-2: Sanitize architecture, RFC, and decision documents under `docs/`
- [x] TASK-3: Sanitize specifications and archive changes under `openspec/`
- [x] TASK-4: Verify complete elimination of invalid patterns and run full test suite

## Verification Evidence
- Full-repo AST regex audit: 0 remaining `\text{..._...}` patterns across all Markdown files.
- Test Suite: 218/218 passing in 15.15s (`.venv/bin/pytest tests/`).
- Commit: `1216087` (`fix/katex-math-subscripts`)

## Next Step
Work unit complete; awaiting user instruction to merge or push branch.
