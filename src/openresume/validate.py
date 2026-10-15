"""Validation for OpenResume documents (XSD for XML, JSON Schema for JSON)."""
import json

from lxml import etree

from .convert import load_json, NS


def validate_xml(source, xsd_path):
    """Validate an XML source (path/bytes/str) against the XSD.

    Returns (ok: bool, errors: list[str]).
    """
    schema = etree.XMLSchema(etree.parse(xsd_path))
    if isinstance(source, bytes):
        doc = etree.fromstring(source)
    elif isinstance(source, str) and source.lstrip().startswith("<"):
        doc = etree.fromstring(source.encode("utf-8"))
    elif hasattr(source, "read"):
        doc = etree.parse(source)
    else:
        doc = etree.parse(source)
    if schema.validate(doc):
        return True, []
    return False, [f"line {e.line}: {e.message}" for e in schema.error_log]


def validate_json(source, schema_path):
    """Validate a JSON source (path/dict/str) against the JSON Schema.

    Returns (ok: bool, errors: list[str]).
    """
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("jsonschema is required for JSON validation: pip install jsonschema") from exc

    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    data = source if isinstance(source, dict) else load_json(source)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return (not errors), [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]
