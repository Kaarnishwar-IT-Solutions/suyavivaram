"""Render an Suyavivaram document (dict) into a modern PDF layout.

The look mirrors the "Modern" theme: a navy header band, blue section rules,
zebra competency tables and tight project blocks. The renderer consumes the
same in-memory dict produced by ``convert.xml_to_dict`` / ``load_json``, so it
is fully decoupled from how the data is stored.
"""
import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, NextPageTemplate,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------- #
# palette (the "Modern" theme)
# --------------------------------------------------------------------------- #
HEADER_BG = HexColor("#1B2A4A")
HEADER_NAME = HexColor("#FFFFFF")
HEADER_TITLE = HexColor("#A0C4E8")
HEADER_CONTACT = HexColor("#CCDDEE")
SECTION = HexColor("#2C5F8A")
RULE = HexColor("#3A7CBD")
BODY = HexColor("#2D2D2D")
MUTED = HexColor("#5A5A5A")
PROJECT_TITLE = HexColor("#1B2A4A")
PROJECT_ROLE = HexColor("#3A7CBD")
TABLE_HEAD = HexColor("#2C5F8A")
ZEBRA = HexColor("#E8F0F7")
GRID = HexColor("#F0F0F0")

PAGE_W, PAGE_H = LETTER
SIDE = 56.0
BOTTOM = 24.0
TOP_GAP = 6.0
PAD_TOP = 10.0
PAD_BOTTOM = 7.0
NAME_SIZE = 24.0
TITLE_SIZE = 10.0
CONTACT_SIZE = 9.0


# --------------------------------------------------------------------------- #
# fonts: prefer Calibri (metric-compatible Carlito / DejaVu fallback)
# --------------------------------------------------------------------------- #
_CANDIDATES = [
    ("Calibri", ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf")),
    ("Carlito", ("Carlito-Regular.ttf", "Carlito-Bold.ttf",
                 "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf")),
    ("DejaVuSans", ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
                    "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf")),
]

_SEARCH_DIRS = [
    r"C:\Windows\Fonts",
    os.path.join(os.path.dirname(__file__), "fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
]


def _locate(filename, roots):
    target = filename.lower()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if f.lower() == target:
                    return os.path.join(dirpath, f)
    return None


def _setup_fonts():
    """Return (family, {regular,bold,italic,boldItalic}, has_ttf)."""
    for family, filenames in _CANDIDATES:
        found = {}
        for key, fn in zip(("regular", "bold", "italic", "boldItalic"), filenames):
            path = _locate(fn, _SEARCH_DIRS)
            if path:
                found[key] = path
        if "regular" not in found or "bold" not in found:
            continue
        try:
            names = {}
            for key, suffix in (("regular", ""), ("bold", "-Bold"),
                                ("italic", "-Italic"), ("boldItalic", "-BoldItalic")):
                if key in found:
                    nm = family + suffix
                    pdfmetrics.registerFont(TTFont(nm, found[key]))
                    names[key] = nm
            registerFontFamily(
                family,
                normal=names["regular"],
                bold=names.get("bold", names["regular"]),
                italic=names.get("italic", names["regular"]),
                boldItalic=names.get("boldItalic", names.get("bold", names["regular"])),
            )
            return family, names, True
        except Exception:  # pragma: no cover - font problems must not break render
            continue
    return "Helvetica", {
        "regular": "Helvetica", "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique", "boldItalic": "Helvetica-BoldOblique",
    }, False


FAMILY, FACES, HAS_TTF = _setup_fonts()


def _glyph_ok(ch):
    """True if the active regular face provides a glyph for ``ch``."""
    try:
        face = pdfmetrics.getFont(FACES["regular"]).face
        return ord(ch) in face.charToGlyph
    except Exception:
        return False


def _pick(preferred, fallback, std):
    if not HAS_TTF:
        return std if not _glyph_ok(fallback) else fallback
    if _glyph_ok(preferred):
        return preferred
    if _glyph_ok(fallback):
        return fallback
    return std


# glyphs that the chosen font actually supports
ARROW = _pick("\u2192", "\u2192", "->")
DOT = _pick("\u25cf", "\u2022", "\u2022")
TRIANGLE = _pick("\u25b8", "\u2022", "-")

_SAFE = {"\u2192": ARROW, "\u2013": "-"}


def _esc(text):
    text = "" if text is None else str(text)
    for k, v in _SAFE.items():
        text = text.replace(k, v)
    return escape(text)


# --------------------------------------------------------------------------- #
# styles
# --------------------------------------------------------------------------- #
def _style(**kw):
    kw.setdefault("fontName", FAMILY)
    kw.setdefault("textColor", BODY)
    return ParagraphStyle("s", **kw)


class _Renderer:
    def __init__(self, data):
        self.data = data
        contact = data.get("contact", {})
        parts = [contact[f] for f in ("location", "email", "phone", "website")
                 if contact.get(f)]
        parts += [p["network"] for p in contact.get("profiles", []) if p.get("network")]
        self.contact_line = "   |   ".join(parts)
        self.title = data.get("title", "")

        self.st = {
            "summary": _style(fontSize=9.5, leading=11, alignment=TA_JUSTIFY),
            "body": _style(fontSize=9.5, leading=12, spaceAfter=3),
            "project_title": _style(fontName=FACES["bold"], fontSize=10,
                                    leading=12.5, textColor=PROJECT_TITLE),
            "project_role": _style(fontName=FACES["italic"], fontSize=9,
                                   leading=11, textColor=PROJECT_ROLE, spaceAfter=1),
            "note": _style(fontSize=9, leading=10.5, textColor=MUTED,
                           leftIndent=9, bulletIndent=0,
                           bulletFontName=FACES["regular"], bulletFontSize=8),
            "skill": _style(fontSize=8.5, leading=10.5),
            "col_title": _style(fontName=FACES["bold"], fontSize=9,
                                leading=11, textColor=HEADER_NAME),
            "th": _style(fontName=FACES["bold"], fontSize=9, leading=11,
                         textColor=HEADER_NAME),
            "td": _style(fontSize=8.5, leading=10.5),
            "period": _style(fontName=FACES["bold"], fontSize=8.5, leading=10.5,
                             textColor=SECTION),
            "role": _style(fontName=FACES["bold"], fontSize=8.5, leading=10.5,
                           textColor=PROJECT_TITLE),
            "edu": _style(fontSize=9.5, leading=12),
            "extra": _style(fontSize=9, leading=11.5, leftIndent=9, bulletIndent=0,
                            bulletFontName=FACES["regular"], bulletFontSize=8),
        }

        self.band_h = self._band_height()

    def _band_height(self):
        h = PAD_TOP + NAME_SIZE * 1.05
        if self.title:
            h += 2 + TITLE_SIZE * 1.35
        if self.contact_line:
            h += 2 + CONTACT_SIZE * 1.3
        return h + PAD_BOTTOM

    # -- header band (drawn on the canvas, first page only) ------------------ #
    def draw_band(self, canvas):
        canvas.saveState()
        canvas.setFillColor(HEADER_BG)
        canvas.rect(0, PAGE_H - self.band_h, PAGE_W, self.band_h, stroke=0, fill=1)

        text = canvas.beginText(SIDE, PAGE_H - PAD_TOP - NAME_SIZE)
        text.setFillColor(HEADER_NAME)
        text.setFont(FACES["bold"], NAME_SIZE)
        text.setLeading(NAME_SIZE * 1.05)
        text.textLine(self.data.get("name", ""))
        if self.title:
            text.moveCursor(0, -2)
            text.setFillColor(HEADER_TITLE)
            text.setFont(FACES["regular"], TITLE_SIZE)
            text.setLeading(TITLE_SIZE * 1.35)
            text.textLine(self.title)
        if self.contact_line:
            text.moveCursor(0, -2)
            text.setFillColor(HEADER_CONTACT)
            text.setFont(FACES["regular"], CONTACT_SIZE)
            text.setLeading(CONTACT_SIZE * 1.3)
            text.textLine(self.contact_line)
        canvas.drawText(text)
        canvas.restoreState()

    # -- content blocks ------------------------------------------------------ #
    def _p(self, markup, style):
        return Paragraph(markup, self.st[style])

    def _section_title(self, title):
        return [
            self._p(f'<font color="#2C5F8A">{_esc(title.upper())}</font>', "project_title"),
            HRFlowable(width="100%", thickness=1.2, color=RULE,
                       spaceBefore=1, spaceAfter=4),
        ]

    def _competencies(self, groups):
        n = len(groups)
        head = [Paragraph(_esc(g["name"]), self.st["col_title"]) for g in groups]
        rows = [head]
        depth = max(len(g["skills"]) for g in groups)
        for i in range(depth):
            rows.append([
                Paragraph(_esc(g["skills"][i]) if i < len(g["skills"]) else "",
                          self.st["skill"])
                for g in groups
            ])
        t = Table(rows, colWidths=[(PAGE_W - 2 * SIDE) / n] * n)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEAD),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 1.5),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        t.setStyle(TableStyle(style))
        return [t, Spacer(1, 5)]

    def _projects(self, projects):
        out = []
        for p in projects:
            block = []
            if p.get("title"):
                block.append(self._p(f'{DOT}&nbsp; {_esc(p["title"])}', "project_title"))
            meta = " | ".join(x for x in (p.get("role"), p.get("company")) if x)
            if p.get("duration"):
                meta = f"{meta}   |   {p['duration']}" if meta else p["duration"]
            if meta:
                block.append(self._p(_esc(meta), "project_role"))
            if p.get("description"):
                block.append(self._p(_esc(p["description"]), "body"))
            if p.get("notes"):
                block += [Paragraph(_esc(n), self.st["note"], bulletText=TRIANGLE)
                          for n in p["notes"]]
            block.append(Spacer(1, 4))
            out.append(KeepTogether(block))
        return out

    def _experience(self, positions):
        head = [Paragraph("Period", self.st["th"]),
                Paragraph("Role", self.st["th"]),
                Paragraph("Organization", self.st["th"])]
        rows = [head]
        for pos in positions:
            rows.append([
                Paragraph(_esc(pos.get("period", "")), self.st["period"]),
                Paragraph(_esc(pos.get("role", "")), self.st["role"]),
                Paragraph(_esc(pos.get("company", "")), self.st["td"]),
            ])
        widths = [105, 110, PAGE_W - 2 * SIDE - 215]
        t = Table(rows, colWidths=widths, repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEAD),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 1.5),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        t.setStyle(TableStyle(style))
        return [t, Spacer(1, 5)]

    def _education(self, degrees):
        out = []
        for d in degrees:
            parts = [f'<b><font color="#1B2A4A">{_esc(d["qualification"])}</font></b>']
            if d.get("institution"):
                parts.append(f'<font color="#5A5A5A">— {_esc(d["institution"])}</font>')
            if d.get("period"):
                parts.append(f'<font color="#5A5A5A">({_esc(d["period"])})</font>')
            out.append(self._p("  ".join(parts), "edu"))
        out.append(Spacer(1, 4))
        return out

    def _languages(self, languages):
        out = []
        for lg in languages:
            detail = " \u2014 ".join(
                x for x in (
                    lg.get("proficiency"),
                    f"({lg['level']})" if lg.get("level") else None,
                ) if x
            )
            text = f'<b><font color="#1B2A4A">{_esc(lg["language"])}</font></b>'
            if detail:
                text += f' <font color="#5A5A5A">{_esc(detail)}</font>'
            out.append(Paragraph(text, self.st["extra"], bulletText=TRIANGLE))
        out.append(Spacer(1, 4))
        return out

    def _additional(self, items):
        return [
            Paragraph(
                f'<b><font color="#1B2A4A">{_esc(it["label"])}:</font></b> '
                f'<font color="#5A5A5A">{_esc(it.get("value", ""))}</font>',
                self.st["extra"], bulletText=TRIANGLE,
            )
            for it in items
        ] + [Spacer(1, 4)]

    def story(self):
        s = []
        if self.data.get("summary"):
            s += self._section_title("Professional Summary")
            s.append(self._p(_esc(self.data["summary"]), "summary"))
        if self.data.get("competencies"):
            s += self._section_title("Core Competencies")
            s += self._competencies(self.data["competencies"])
        if self.data.get("projects"):
            s += self._section_title("Key Projects")
            s += self._projects(self.data["projects"])
        if self.data.get("experience"):
            s += self._section_title("Professional Experience")
            s += self._experience(self.data["experience"])
        if self.data.get("education"):
            s += self._section_title("Education")
            s += self._education(self.data["education"])
        if self.data.get("languages"):
            s += self._section_title("Languages")
            s += self._languages(self.data["languages"])
        if self.data.get("additional"):
            s += self._section_title("Additional Details")
            s += self._additional(self.data["additional"])
        return s


def render_pdf(data, out_path, embed=None):
    """Render ``data`` (Suyavivaram dict) to ``out_path`` (PDF).

    ``embed`` is an optional ``(filename, bytes)`` pair attached to the PDF so
    the machine-readable source travels with the human-readable layout.
    """
    name = (data.get("name") or "Resume").strip()
    renderer = _Renderer(data)

    doc = BaseDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=SIDE, rightMargin=SIDE, topMargin=BOTTOM, bottomMargin=BOTTOM,
        title=f"{name} — Resume", author=name, subject="Suyavivaram",
    )
    frame_first = Frame(SIDE, BOTTOM, doc.width,
                        PAGE_H - renderer.band_h - TOP_GAP - BOTTOM, id="first")
    frame_later = Frame(SIDE, BOTTOM, doc.width, PAGE_H - BOTTOM * 2, id="later")
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[frame_first],
                     onPage=lambda c, d: renderer.draw_band(c)),
        PageTemplate(id="later", frames=[frame_later], onPage=lambda c, d: None),
    ])
    doc.build([NextPageTemplate("later")] + renderer.story())

    if embed:
        _embed(out_path, embed[0], embed[1])
    return out_path


def _embed(pdf_path, filename, data):
    try:
        import fitz  # PyMuPDF
    except ImportError:  # pragma: no cover
        return
    doc = fitz.open(pdf_path)
    doc.embfile_add(filename, data)
    tmp = pdf_path + ".tmp"
    doc.save(tmp, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp, pdf_path)
