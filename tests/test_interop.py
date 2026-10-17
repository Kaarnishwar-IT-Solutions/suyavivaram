"""JSON Resume interoperability: import, export and round-trip."""
from pathlib import Path

from suyavivaram.convert import xml_to_dict
from suyavivaram.interop import from_jsonresume, to_jsonresume

ROOT = Path(__file__).resolve().parents[1]
EX_XML = ROOT / "examples" / "resume.xml"

JSON_RESUME = {
    "basics": {
        "name": "Jane Doe",
        "label": "Web Developer",
        "email": "jane@example.com",
        "phone": "(912) 555-4321",
        "url": "https://jane.example.com",
        "summary": "Full stack developer.",
        "location": {"address": "2712 Broadway St", "city": "San Francisco",
                     "region": "California", "countryCode": "US"},
        "profiles": [
            {"network": "Twitter", "username": "jane", "url": "https://twitter.com/jane"},
            {"network": "LinkedIn", "username": "jane-doe", "url": "https://linkedin.com/in/jane-doe"},
        ],
    },
    "work": [
        {"name": "Company", "position": "President",
         "startDate": "2013-01-01", "endDate": "2014-01-01",
         "highlights": ["Did a thing"]},
    ],
    "education": [
        {"institution": "University", "area": "Software Development",
         "studyType": "Bachelor", "startDate": "2011", "endDate": "2013"},
    ],
    "skills": [
        {"name": "Web Development", "level": "Master",
         "keywords": ["HTML", "CSS", "JavaScript"]},
    ],
    "languages": [
        {"language": "English", "fluency": "Native"},
        {"language": "Spanish", "fluency": "Professional working proficiency"},
    ],
    "projects": [
        {"name": "JSON Resume", "description": "Open standard",
         "highlights": ["10K stars"], "roles": ["Maintainer"],
         "entity": "Community", "startDate": "2014"},
    ],
}


def test_import_jsonresume():
    d = from_jsonresume(JSON_RESUME)
    assert d["name"] == "Jane Doe"
    assert d["title"] == "Web Developer"
    assert d["contact"]["email"] == "jane@example.com"
    assert d["contact"]["location"] == "San Francisco, California, US"
    assert d["contact"]["profiles"][0]["network"] == "Twitter"
    assert d["experience"][0] == {"period": "2013-01-01 – 2014-01-01",
                                  "role": "President", "company": "Company"}
    assert d["education"][0]["qualification"] == "Bachelor Software Development"
    assert d["competencies"][0]["skills"] == ["HTML", "CSS", "JavaScript"]
    assert d["languages"][0] == {"language": "English", "proficiency": "Native"}
    assert d["projects"][0]["title"] == "JSON Resume"


def test_export_shape():
    data = xml_to_dict(EX_XML)
    jr = to_jsonresume(data)
    assert set(jr) == {"basics", "work", "education", "skills", "languages", "projects"}
    assert jr["basics"]["name"] == data["name"]
    assert jr["basics"]["profiles"][0]["network"] == "LinkedIn"
    assert jr["languages"][0]["language"] == "English"


def test_cefr_level_survives_via_fluency():
    data = xml_to_dict(EX_XML)
    jr = to_jsonresume(data)
    assert jr["languages"][0]["fluency"] == "Native (C2)"
    back = from_jsonresume(jr)
    assert back["languages"][0] == {"language": "English", "proficiency": "Native", "level": "C2"}


def test_full_roundtrip_preserves_mapped_sections():
    original = xml_to_dict(EX_XML)
    back = from_jsonresume(to_jsonresume(original))
    for key in ("name", "title", "summary", "contact", "competencies",
                "projects", "experience", "education", "languages"):
        assert back.get(key) == original.get(key), key
