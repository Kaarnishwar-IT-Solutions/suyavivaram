"""Lossless conversion between OpenResume XML and its JSON form.

Both representations describe the same model, defined by ``schema/resume.xsd``
and ``schema/resume.schema.json``. Round-tripping is lossless.
"""
import json
import os

from lxml import etree

NS = "urn:openresume:2.0"
NSMAP = {None: NS}
_Q = "{%s}" % NS

CONTACT_FIELDS = ("email", "phone", "location", "website", "linkedin", "github")
PROJECT_FIELDS = ("company", "role", "duration", "description")


# --------------------------------------------------------------------------- #
# parsing helpers
# --------------------------------------------------------------------------- #
def _t(el):
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _text_opt(parent, name):
    el = parent.find(name)
    return _t(el) if el is not None else None


def _strip_ns(el):
    for node in el.iter():
        if isinstance(node.tag, str) and node.tag.startswith("{"):
            node.tag = etree.QName(node).localname
    etree.cleanup_namespaces(el)
    return el


def parse_xml(source):
    """Parse XML from a path, an XML string/bytes, or a file-like object.

    Returns the (namespace-stripped) root element so callers can use plain tags.
    """
    if isinstance(source, bytes):
        root = etree.fromstring(source)
    elif isinstance(source, str) and source.lstrip().startswith("<"):
        root = etree.fromstring(source.encode("utf-8"))
    elif hasattr(source, "read"):
        root = etree.parse(source).getroot()
    else:
        root = etree.parse(source).getroot()
    return _strip_ns(root)


def load_json(source):
    if hasattr(source, "read"):
        return json.load(source)
    if isinstance(source, (bytes, bytearray)):
        return json.loads(source.decode("utf-8"))
    if isinstance(source, os.PathLike):
        with open(source, encoding="utf-8") as fh:
            return json.load(fh)
    if isinstance(source, str):
        if source.lstrip().startswith("{"):
            return json.loads(source)
        with open(source, encoding="utf-8") as fh:
            return json.load(fh)
    raise TypeError("unsupported JSON source")


# --------------------------------------------------------------------------- #
# XML -> dict
# --------------------------------------------------------------------------- #
def xml_to_dict(source):
    root = parse_xml(source)
    data = {"version": root.get("version") or "2.0"}
    data["name"] = _t(root.find("name"))

    title = _text_opt(root, "title")
    if title is not None:
        data["title"] = title

    c = root.find("contact")
    if c is not None:
        contact = {f: v for f in CONTACT_FIELDS if (v := _text_opt(c, f)) is not None}
        if contact:
            data["contact"] = contact

    summary = _text_opt(root, "summary")
    if summary is not None:
        data["summary"] = summary

    comp = root.find("competencies")
    if comp is not None:
        data["competencies"] = [
            {"name": g.get("name"), "skills": [_t(s) for s in g.findall("skill")]}
            for g in comp.findall("group")
        ]

    prj = root.find("projects")
    if prj is not None:
        projects = []
        for p in prj.findall("project"):
            proj = {"title": _t(p.find("title"))}
            for f in PROJECT_FIELDS:
                v = _text_opt(p, f)
                if v is not None:
                    proj[f] = v
            notes = p.find("notes")
            if notes is not None:
                proj["notes"] = [_t(n) for n in notes.findall("note")]
            projects.append(proj)
        data["projects"] = projects

    exp = root.find("experience")
    if exp is not None:
        positions = []
        for pos in exp.findall("position"):
            entry = {"role": _t(pos.find("role")), "company": _t(pos.find("company"))}
            period = _text_opt(pos, "period")
            if period is not None:
                entry["period"] = period
            positions.append(entry)
        data["experience"] = positions

    edu = root.find("education")
    if edu is not None:
        degrees = []
        for dg in edu.findall("degree"):
            deg = {"qualification": _t(dg.find("qualification"))}
            for f in ("institution", "period"):
                v = _text_opt(dg, f)
                if v is not None:
                    deg[f] = v
            degrees.append(deg)
        data["education"] = degrees

    ad = root.find("additional")
    if ad is not None:
        data["additional"] = [
            {"label": it.get("label"), "value": _t(it)} for it in ad.findall("item")
        ]
    return data


# --------------------------------------------------------------------------- #
# dict -> XML
# --------------------------------------------------------------------------- #
def _sub(parent, name, text=None):
    el = etree.SubElement(parent, _Q + name)
    if text is not None:
        el.text = text
    return el


def dict_to_xml(data):
    root = etree.Element(_Q + "resume", nsmap=NSMAP)
    root.set("version", str(data.get("version", "2.0")))

    _sub(root, "name", data.get("name", ""))
    if data.get("title"):
        _sub(root, "title", data["title"])

    if data.get("contact"):
        c = _sub(root, "contact")
        for field in CONTACT_FIELDS:
            if data["contact"].get(field):
                _sub(c, field, data["contact"][field])

    if data.get("summary"):
        _sub(root, "summary", data["summary"])

    if data.get("competencies"):
        comp = _sub(root, "competencies")
        for g in data["competencies"]:
            gel = _sub(comp, "group")
            gel.set("name", g["name"])
            for s in g["skills"]:
                _sub(gel, "skill", s)

    if data.get("projects"):
        prj = _sub(root, "projects")
        for p in data["projects"]:
            pel = _sub(prj, "project")
            _sub(pel, "title", p["title"])
            for field in PROJECT_FIELDS:
                if p.get(field):
                    _sub(pel, field, p[field])
            if p.get("notes"):
                nel = _sub(pel, "notes")
                for n in p["notes"]:
                    _sub(nel, "note", n)

    if data.get("experience"):
        exp = _sub(root, "experience")
        for pos in data["experience"]:
            pel = _sub(exp, "position")
            if pos.get("period"):
                _sub(pel, "period", pos["period"])
            _sub(pel, "role", pos["role"])
            _sub(pel, "company", pos["company"])

    if data.get("education"):
        edu = _sub(root, "education")
        for dg in data["education"]:
            del_ = _sub(edu, "degree")
            _sub(del_, "qualification", dg["qualification"])
            for field in ("institution", "period"):
                if dg.get(field):
                    _sub(del_, field, dg[field])

    if data.get("additional"):
        ad = _sub(root, "additional")
        for it in data["additional"]:
            el = _sub(ad, "item", it.get("value", ""))
            el.set("label", it["label"])

    return root


# --------------------------------------------------------------------------- #
# public string/bytes helpers
# --------------------------------------------------------------------------- #
def to_xml_string(data):
    root = dict_to_xml(data)
    return etree.tostring(
        root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    ).decode("utf-8")


def to_json_string(data, indent=2):
    return json.dumps(data, indent=indent, ensure_ascii=False)


def xml_to_json(source, indent=2):
    return to_json_string(xml_to_dict(source), indent=indent)


def json_to_xml(source):
    return to_xml_string(load_json(source))
