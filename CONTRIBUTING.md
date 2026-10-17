# Contributing to Suyavivaram

Thanks for helping improve an open resume format.

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

Open an issue describing the document, the expected result, and the actual result.
If possible attach a minimal `resume.xml`/`resume.json`.
