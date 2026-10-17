# OpenResume

**The XML/JSON is the source of truth. The PDF is just one rendering.**

OpenResume is an open, renderer-agnostic resume format plus a small toolkit.
Anyone can read, validate, diff, convert and render a resume — so it can power
a personal CV, a website's auto-builder, or an AI resume handler.

```
resume.xml  ⇄  resume.json          (source of truth, one model)
      │
      ▼
  render (PDF)   →   self-describing PDF (source attached)
```

> Named in the spirit of **Peppol** — open, reusable, structured documents that
> render to a human-readable form. (Peppol defines procurement documents, not
> resumes; OpenResume borrows the *interoperability* principle.)

## Why

- **One model, many renderings.** Author once; render to PDF now, HTML/DOCX later.
- **Open and portable.** MIT licensed. Plain XML/JSON, no lock-in, no account.
- **Machine + AI friendly.** A strict schema makes automated parsing and generation reliable.
- **Self-describing output.** The rendered PDF carries its own source XML/JSON.
- **Zero-dependency to consume.** Read the JSON, or validate the XML against the XSD.
- **Interoperable.** Import/export **JSON Resume**, and mirror Europass's CEFR language levels.

## Install

```bash
pip install openresume
```

From source:

```bash
pip install -e .
```

## Use

```bash
openresume validate resume.xml      # or resume.json
openresume convert  resume.xml resume.json
openresume render   resume.xml -o resume.pdf
openresume serve                     # local web validator & preview (http://127.0.0.1:8000)
openresume from-jsonresume resume.json -o resume.xml   # JSON Resume -> OpenResume
openresume to-jsonresume   resume.xml  -o resume.json   # OpenResume -> JSON Resume
```

As a library:

```python
from openresume import xml_to_dict, to_json_string
from openresume.render import render_pdf

data = xml_to_dict("resume.xml")
render_pdf(data, "resume.pdf", embed=("resume.xml", open("resume.xml", "rb").read()))
```

## Validate online

Two ways to try it without installing anything:

- **Static web app** — open `docs/index.html` (published on GitHub Pages). Paste
  XML or JSON, validate against the schema in the browser, and preview the
  "Modern" theme live. Use *Print / Save as PDF* to export.
- **Local server** — `openresume serve` runs the same page plus real XSD/XSD and
  real PDF endpoints (`/api/validate`, `/api/render`).

On a website: fetch `resume.json`, validate against
`schema/resume.schema.json`, render with your own template. The JSON model is the
contract — the PDF renderer here is only a reference implementation.

## The format

One model with **named fields**, in two equivalent serialisations:

| | XML | JSON |
|---|---|---|
| Spec | `schema/resume.xsd` | `schema/resume.schema.json` |
| Namespace / `$id` | `urn:openresume:2.0` | `urn:openresume:2.0` |

| Part | XML | JSON | Renders as |
|---|---|---|---|
| name | `<name>` | `name` | header title |
| title | `<title>` | `title` | header subtitle |
| contact | `<contact><email/>…</contact>` | `contact: {email, phone, location, website}` | header contact line |
| social profiles | `<profile network="…">url</profile>` | `contact.profiles: [{network, username, url}]` | header (network names) |
| summary | `<summary>` | `summary` | paragraph |
| competencies | `<group name><skill/></group>` | `competencies: [{name, skills}]` | multi-column table |
| projects | `<project><title/><notes><note/></notes></project>` | `projects: [{title, notes}]` | titled blocks |
| experience | `<position><role/><company/></position>` | `experience: [{role, company}]` | table |
| education | `<degree><qualification/></degree>` | `education: [{qualification}]` | lines |
| languages | `<language proficiency="…" level="…">name</language>` | `languages: [{language, proficiency, level}]` | bullet list |
| additional | `<item label>value</item>` | `additional: [{label, value}]` | bullet list |

`profiles` and `languages` use the same key names as **JSON Resume**, and
`level` carries an optional **CEFR** code (A1–C2) as in **Europass**.

See **[spec/SPEC.md](spec/SPEC.md)** for the full specification and
**[examples/](examples/)** for complete files (`resume.xml`, `resume.json`).

## Repository layout

```
schema/     resume.xsd, resume.schema.json   # the format
spec/       SPEC.md                           # the specification
examples/   resume.xml, resume.json           # full examples
src/openresume/                               # toolkit (convert, validate, render, interop, serve, cli)
docs/                                         # static GitHub Pages validator & preview
tests/                                        # pytest suite
```

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)**. The schema is versioned; changes go
through the spec.

## License

MIT © 2026 Kaarnishwar IT Solutions — see [LICENSE](LICENSE).
