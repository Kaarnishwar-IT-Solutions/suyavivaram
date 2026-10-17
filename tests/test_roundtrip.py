"""Lossless round-trip tests between XML and JSON forms."""
from pathlib import Path

from suyavivaram import to_xml_string, xml_to_dict, xml_to_json
from suyavivaram.convert import load_json

ROOT = Path(__file__).resolve().parents[1]
EX_XML = ROOT / "examples" / "resume.xml"
EX_JSON = ROOT / "examples" / "resume.json"


def test_example_has_content():
    d = xml_to_dict(EX_XML)
    assert d["name"]
    assert d["title"]
    assert len(d["competencies"]) >= 2
    assert len(d["projects"]) >= 3
    assert len(d["experience"]) >= 2
    assert d["contact"]["profiles"]
    assert d["languages"]


def test_projects_have_named_fields():
    d = xml_to_dict(EX_XML)
    p = d["projects"][0]
    assert p["title"]
    assert "company" in p and "role" in p
    assert p["notes"]


def test_dict_roundtrip_is_stable():
    d1 = xml_to_dict(EX_XML)
    d2 = xml_to_dict(to_xml_string(d1))
    assert d1 == d2


def test_json_matches_xml():
    assert load_json(EX_JSON) == xml_to_dict(EX_XML)


def test_xml_to_json_is_parseable():
    import json

    assert json.loads(xml_to_json(EX_XML))["name"]
