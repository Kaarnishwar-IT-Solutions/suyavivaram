# Changelog

All notable changes to this project are documented here.
The format is versioned by `MAJOR.MINOR` for the schema; the toolkit uses semver.

## [2.0.0] - 2026-10-14

### Changed (breaking)
- **Format v2.0** (`urn:openresume:2.0`): named, domain-specific fields replace
  the generic v1 `header`/`section` model. Document is now `name`, `title`,
  `contact`, `summary`, `competencies`, `projects`, `experience`, `education`,
  `additional`. v1 documents are not valid v2 documents.
- Reference renderer now emits a "Modern"-themed **Letter**-size PDF
  (navy header band, Calibri, blue section rules) instead of the old A4 layout.

### Added
- `openresume serve` — local web validator & preview (stdlib HTTP server).
- `docs/` — static, client-side validator & live preview for GitHub Pages.
- GitHub Pages workflow (`.github/workflows/pages.yml`).

### Changed
- `convert`, `validate`, tests, examples and the Python API updated for v2.

## [1.0.0] - 2026-10-14

### Added
- OpenResume v1.0 format:
  - XML schema `schema/resume.xsd` (namespace `urn:openresume:1.0`).
  - JSON Schema `schema/resume.schema.json` (Draft 2020-12).
  - Specification `spec/SPEC.md`.
- Toolkit (`openresume`):
  - `convert` — lossless XML ⇄ JSON.
  - `validate` — XSD / JSON Schema validation.
  - `render` — A4 PDF reference renderer; embeds the source document.
  - CLI (`openresume`) and Python API.
- Examples (`examples/resume.xml`, `examples/resume.json`) and a pytest suite.
- GitHub Actions CI (lint-validate + tests on Python 3.9–3.12).
