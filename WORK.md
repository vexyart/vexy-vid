---
this_file: WORK.md
---

# Work log

## 2026-11-24: documentation theme

- Rebuilt `docs/` with fly-january 0.1.1 and `chrome: none`. The header,
  repository link and table of contents use unbranded labels.
- `./build.sh docs` passed in strict mode with zero warnings. The five local
  Fly assets match the installed theme. Search indexes all 11 documentation pages.
- `pytest tests/ --cov=vexy_vid --cov-report=term-missing` passed all 49 tests,
  including seven ffmpeg integration tests (63% coverage).

## 2026-10-18: documentation plugins

- Use MaterialX search, inherited metadata and a topic index; keep ordered navigation in awesome-nav.
- The documentation wrapper installs the plugins required by this site.
- Strict documentation build and rendered output checks passed.
