# OpenResume Format Specification — v2.0

- **Identifier:** `urn:openresume:2.0`
- **Status:** stable
- **Licence:** MIT

OpenResume defines a single logical resume model with two normative
serialisations: XML (schema: `resume.xsd`) and JSON (schema: `resume.schema.json`).
The two are losslessly convertible. A renderer consumes the model; it does not
read the serialisation. v2.0 introduces **named, domain-specific fields** (name,
title, contact, summary, competencies, projects, experience, education,
additional) replacing the generic `header`/`section` model of v1.0.

## 1. Conformance

A document is **conformant** if it validates against the relevant schema:

- XML against `schema/resume.xsd` (namespace `urn:openresume:2.0`).
- JSON against `schema/resume.schema.json` (Draft 2020-12).

## 2. Document

```
Resume
  version      : string             (optional; default "2.0")
  name         : string             (required)
  title        : string             (optional)  - headline/tagline
  contact      : Contact            (optional)
  summary      : string             (optional)  - one paragraph
  competencies : CompetencyGroup[]  (optional, >= 1)
  projects     : Project[]          (optional, >= 1)
  experience   : Position[]         (optional, >= 1)
  education    : Degree[]           (optional, >= 1)
  additional   : AdditionalItem[]   (optional, >= 1)
```

Elements appear in the order above (XML `xs:sequence`). Every field except
`name` is optional; a consumer MUST ignore no field it does not understand
within the model, and unknown fields are rejected by the schema.

## 3. Contact

```
Contact                       (all fields optional, any order — XML xs:all)
  email    : string
  phone    : string
  location : string
  website  : string
  linkedin : string
  github   : string
```

## 4. Competencies

```
CompetencyGroup
  name   : string      (required)  - XML attribute `name`
  skills : string[]    (required, >= 1)
```

## 5. Projects

```
Project
  title       : string     (required)
  company     : string     (optional)
  role        : string     (optional)
  duration    : string     (optional)  - free text, e.g. "Apr 2025 – Present"
  description : string     (optional)  - one paragraph
  notes       : string[]   (optional)  - bullet highlights
```

## 6. Experience

```
Position
  period  : string   (optional)
  role    : string   (required)
  company : string   (required)
```

## 7. Education

```
Degree
  qualification : string   (required)
  institution   : string   (optional)
  period        : string   (optional)
```

## 8. Additional

```
AdditionalItem
  label : string   (required)  - XML attribute `label`
  value : string   (required)
```

## 9. XML ⇄ JSON mapping

| Model | XML | JSON |
|---|---|---|
| name | `<name>` | `name` |
| title | `<title>` | `title` |
| contact | `<contact><email/><phone/>…</contact>` | `contact: {email, phone, …}` |
| summary | `<summary>` | `summary` |
| competency group | `<group name="…"><skill/></group>` | `{name, skills: []}` |
| project | `<project><title/><company/><role/><duration/><description/><notes><note/></notes></project>` | `{title, company, role, duration, description, notes: []}` |
| position | `<position><period/><role/><company/></position>` | `{period, role, company}` |
| degree | `<degree><qualification/><institution/><period/></degree>` | `{qualification, institution, period}` |
| additional item | `<item label="…">value</item>` | `{label, value}` |

## 10. Namespaces & versioning

- XML namespace: `urn:openresume:2.0`. The root element MUST be in this namespace.
- JSON documents MAY carry `"$schema": "urn:openresume:2.0"`.
- `version` communicates the format version and defaults to `"2.0"`.
- Backwards-incompatible changes increment the major version and the namespace.
  Additive, optional fields keep the same major version.
- v1.0 documents (`urn:openresume:1.0`, `header`/`section`) are **not** valid
  v2.0 documents. A v1→v2 migration is a restructure, not a rename.

## 11. Round-trip guarantee

`xml_to_dict` ∘ `to_xml_string` is lossless for conformant documents:
`xml_to_dict(to_xml_string(xml_to_dict(doc))) == xml_to_dict(doc)`.
Whitespace in text is trimmed; no other normalisation is applied.

## 12. Rendering (non-normative)

Rendering to PDF, HTML, DOCX, etc. is implementation-defined. The reference
renderer emits a "Modern"-themed Letter-size PDF and MAY attach the source
document as an embedded file so the output is self-describing. A renderer MUST
NOT require information not present in the model.

## 13. Extension

Unknown/optional data for a given deployment SHOULD be carried in separate
namespaced elements/keys so conformant readers can ignore it. Such extensions
are out of scope for v2.0 of this specification.
