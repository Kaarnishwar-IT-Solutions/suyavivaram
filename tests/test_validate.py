"""Schema validation tests (XSD for XML, JSON Schema for JSON)."""
from pathlib import Path

import pytest

from openresume.validate import validate_json, validate_xml

ROOT = Path(__file__).resolve().parents[1]
XSD = ROOT / "schema" / "resume.xsd"
JSON_SCHEMA = ROOT / "schema" / "resume.schema.json"
EX_XML = ROOT / "examples" / "resume.xml"
EX_JSON = ROOT / "examples" / "resume.json"


def test_example_xml_valid():
    ok, errors = validate_xml(EX_XML, XSD)
    assert ok, errors


def test_example_json_valid():
    ok, errors = validate_json(EX_JSON, JSON_SCHEMA)
    assert ok, errors


def test_missing_name_is_invalid_xml():
    bad = ('<?xml version="1.0"?>'
           '<resume xmlns="urn:openresume:2.0"><title>No name</title></resume>')
    ok, errors = validate_xml(bad, XSD)
    assert not ok
    assert errors


def test_missing_name_is_invalid_json():
    pytest.importorskip("jsonschema")
    ok, errors = validate_json({"title": "No name"}, JSON_SCHEMA)
    assert not ok
    assert errors


def test_unknown_field_is_invalid_json():
    pytest.importorskip("jsonschema")
    ok, errors = validate_json({"name": "X", "unexpected": True}, JSON_SCHEMA)
    assert not ok
    assert errors


def test_project_without_title_is_invalid_json():
    pytest.importorskip("jsonschema")
    bad = {"name": "X", "projects": [{"company": "Acme"}]}
    ok, errors = validate_json(bad, JSON_SCHEMA)
    assert not ok
    assert errors
