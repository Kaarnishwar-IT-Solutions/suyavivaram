"""The published schema/examples and the bundled package copies must not drift."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "suyavivaram" / "data"
DOCS = ROOT / "docs"

PAIRS = [
    (ROOT / "schema" / "resume.xsd", DATA / "resume.xsd"),
    (ROOT / "schema" / "resume.schema.json", DATA / "resume.schema.json"),
    (ROOT / "examples" / "resume.xml", DATA / "example.resume.xml"),
    (ROOT / "schema" / "resume.schema.json", DOCS / "resume.schema.json"),
    (ROOT / "examples" / "resume.xml", DOCS / "example.resume.xml"),
    (ROOT / "examples" / "resume.json", DOCS / "example.resume.json"),
]


def test_data_copies_in_sync():
    for pub, bundled in PAIRS:
        assert bundled.exists(), f"missing bundled copy: {bundled}"
        assert pub.read_bytes() == bundled.read_bytes(), f"out of sync: {pub.name}"
