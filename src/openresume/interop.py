"""Interoperability with the JSON Resume standard (https://jsonresume.org).

OpenResume deliberately does not try to replace JSON Resume; it bridges to it.
:func:`from_jsonresume` reads a ``resume.json`` (JSON Resume) document into the
OpenResume model; :func:`to_jsonresume` exports the other way. Mapping covers the
overlapping sections (basics, work, education, skills, projects, languages).

Sections JSON Resume has but OpenResume does not model in this version
(awards, certificates, publications, volunteer, interests, references, meta)
are not imported. The mapping is intentionally best-effort: free-text periods
are exchanged with JSON Resume's ``startDate`` field.
"""
import json
import re

from .convert import load_json

# JSON Resume has no CEFR field, so a level is carried inside ``fluency``
# (e.g. "Native (C2)") and split back out on import.
_CEFR = re.compile(r"^(?P<label>.*?)\s*\((?P<level>[A-C][12])\)\s*$")


def _fluency(lg):
    prof, lvl = lg.get("proficiency"), lg.get("level")
    if prof and lvl:
        return f"{prof} ({lvl})"
    return prof or lvl or None


def _split_fluency(fluency):
    if not fluency:
        return None, None
    m = _CEFR.match(fluency.strip())
    if m:
        return m.group("label").strip() or None, m.group("level")
    return fluency.strip() or None, None

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _period(start, end):
    start = (start or "").strip()
    end = (end or "").strip()
    if start and end:
        return f"{start} \u2013 {end}"
    return start or end or None


def _dates_from_period(period):
    """Best-effort: put the free-text period into JSON Resume ``startDate``."""
    return (period or "").strip() or None


def _clean(d):
    return {k: v for k, v in d.items() if v}


def _location_to_string(loc):
    if not loc:
        return None
    if isinstance(loc, str):
        return loc.strip() or None
    parts = [loc.get("city"), loc.get("region"), loc.get("countryCode")]
    joined = ", ".join(p for p in parts if p)
    return joined or (loc.get("address") or "").strip() or None


# --------------------------------------------------------------------------- #
# JSON Resume -> OpenResume
# --------------------------------------------------------------------------- #
def from_jsonresume(source):
    jr = source if isinstance(source, dict) else load_json(source)
    data = {"version": "2.0"}

    basics = jr.get("basics") or {}
    data["name"] = (basics.get("name") or "").strip()
    if basics.get("label"):
        data["title"] = basics["label"]

    contact = _clean({
        "email": basics.get("email"),
        "phone": basics.get("phone"),
        "location": _location_to_string(basics.get("location")),
        "website": basics.get("url"),
    })
    profiles = []
    for p in basics.get("profiles") or []:
        prof = _clean({
            "network": p.get("network"),
            "username": p.get("username"),
            "url": p.get("url"),
        })
        if prof.get("network"):
            profiles.append(prof)
    if profiles:
        contact["profiles"] = profiles
    if contact:
        data["contact"] = contact

    if basics.get("summary"):
        data["summary"] = basics["summary"]

    work = jr.get("work") or []
    if work:
        data["experience"] = [
            _clean({
                "period": _period(w.get("startDate"), w.get("endDate")),
                "role": (w.get("position") or "").strip(),
                "company": (w.get("name") or w.get("company") or "").strip(),
            })
            for w in work
        ]

    education = jr.get("education") or []
    if education:
        out = []
        for e in education:
            parts = [e.get("studyType"), e.get("area")]
            qualification = " ".join(p for p in parts if p).strip() or (e.get("institution") or "").strip()
            out.append(_clean({
                "qualification": qualification,
                "institution": (e.get("institution") or "").strip() or None,
                "period": _period(e.get("startDate"), e.get("endDate")),
            }))
        data["education"] = out

    skills = jr.get("skills") or []
    if skills:
        data["competencies"] = []
        for s in skills:
            name = (s.get("name") or "").strip()
            keywords = [k for k in (s.get("keywords") or []) if k]
            if not name and not keywords:
                continue
            data["competencies"].append({
                "name": name or (keywords[0] if keywords else "Skills"),
                "skills": keywords or [name],
            })

    languages = jr.get("languages") or []
    if languages:
        data["languages"] = []
        for lg in languages:
            name = (lg.get("language") or "").strip()
            if not name:
                continue
            prof, lvl = _split_fluency(lg.get("fluency") or lg.get("proficiency"))
            data["languages"].append(_clean({
                "language": name, "proficiency": prof, "level": lvl,
            }))

    projects = jr.get("projects") or []
    if projects:
        out = []
        for p in projects:
            title = (p.get("name") or "").strip()
            if not title:
                continue
            roles = p.get("roles") or []
            out.append(_clean({
                "title": title,
                "company": p.get("entity"),
                "role": roles[0] if roles else None,
                "duration": _period(p.get("startDate"), p.get("endDate")),
                "description": p.get("description"),
                "notes": [h for h in (p.get("highlights") or []) if h],
            }))
        data["projects"] = out

    return data


# --------------------------------------------------------------------------- #
# OpenResume -> JSON Resume
# --------------------------------------------------------------------------- #
def to_jsonresume(data):
    contact = data.get("contact") or {}
    basics = _clean({
        "name": data.get("name"),
        "label": data.get("title"),
        "email": contact.get("email"),
        "phone": contact.get("phone"),
        "url": contact.get("website"),
        "summary": data.get("summary"),
    })
    if contact.get("location"):
        basics["location"] = {"address": contact["location"]}
    if contact.get("profiles"):
        basics["profiles"] = [
            _clean({
                "network": p.get("network"),
                "username": p.get("username"),
                "url": p.get("url"),
            })
            for p in contact["profiles"]
        ]

    jr = {"basics": basics}

    if data.get("experience"):
        jr["work"] = [
            _clean({
                "name": pos.get("company"),
                "position": pos.get("role"),
                "startDate": _dates_from_period(pos.get("period")),
            })
            for pos in data["experience"]
        ]

    if data.get("education"):
        jr["education"] = [
            _clean({
                "institution": d.get("institution"),
                "studyType": d.get("qualification"),
                "startDate": _dates_from_period(d.get("period")),
            })
            for d in data["education"]
        ]

    if data.get("competencies"):
        jr["skills"] = [
            _clean({"name": g.get("name"), "keywords": g.get("skills")})
            for g in data["competencies"]
        ]

    if data.get("languages"):
        jr["languages"] = [
            _clean({"language": lg.get("language"), "fluency": _fluency(lg)})
            for lg in data["languages"]
        ]

    if data.get("projects"):
        jr["projects"] = [
            _clean({
                "name": p.get("title"),
                "description": p.get("description"),
                "highlights": p.get("notes"),
                "entity": p.get("company"),
                "roles": [p["role"]] if p.get("role") else None,
                "startDate": _dates_from_period(p.get("duration")),
            })
            for p in data["projects"]
        ]

    return jr


def to_jsonresume_string(data, indent=2):
    return json.dumps(to_jsonresume(data), indent=indent, ensure_ascii=False)
