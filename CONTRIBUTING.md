# Contributing to Suyavivaram

Thanks for helping improve an open resume format.

## Ways to contribute

- **Report a bug** or **request a feature** — use the issue forms (they ask for the
  details we need, including a minimal document).
- **Propose a format change** — use the *Schema / format change* issue form; read the
  versioning rules below first.
- **Pick up a `good first issue`** — small, well-scoped tasks labelled for newcomers:
  <https://github.com/Kaarnishwar-IT-Solutions/suyavivaram/labels/good%20first%20issue>.
- **Improve docs** — README, `spec/SPEC.md`, examples, or the browser validator.
- **Add a renderer or an interop converter** — e.g. an HTML/DOCX renderer or another
  ecosystem's format.

## Ground rules

- The format is **versioned**. Backwards-incompatible changes bump the major
  version and the XML namespace (`urn:suyavivaram:N.0`). Additive optional fields
  do not.
- The XML and JSON serialisations must stay **losslessly convertible**.
- Every schema change needs: updated `schema/resume.xsd`, `schema/resume.schema.json`,
  the mirrored copies in `src/suyavivaram/data/` **and `docs/`**, the spec
  (`spec/SPEC.md`), the changelog, and tests.
- The browser validator (`docs/app.js`) must stay behaviourally in sync with the
  Python converter (`src/suyavivaram/convert.py`).

## Development setup

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows; use bin/activate on POSIX
pip install -e ".[dev]"
```

## Checks before a PR

```bash
pytest
suyavivaram validate examples/resume.xml
suyavivaram validate examples/resume.json
```

The `schema/` and `src/suyavivaram/data/` copies must be identical
(`tests/test_schema_sync.py` enforces this).

## Style

- Python: stdlib + declared deps only; keep the converter/renderer small and side-effect free.
- Commits: imperative mood, one logical change each.

## Reporting issues

Use the GitHub issue forms — they ask for the document, the expected result, and the
actual result. If possible, attach a minimal `resume.xml` / `resume.json`.

## Pull requests

The PR template lists the checks we look for. In short: keep the change focused, run the
checks above, keep the schema copies in sync, and never commit personal data (use the
fictional example data).
