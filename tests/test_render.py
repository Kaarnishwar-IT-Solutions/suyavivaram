"""Rendering tests."""
from pathlib import Path

import pytest

from openresume import xml_to_dict

ROOT = Path(__file__).resolve().parents[1]
EX_XML = ROOT / "examples" / "resume.xml"


def test_render_produces_pdf(tmp_path):
    pytest.importorskip("reportlab")
    from openresume.render import render_pdf

    out = tmp_path / "resume.pdf"
    render_pdf(xml_to_dict(EX_XML), str(out))
    assert out.exists()
    assert out.stat().st_size > 1000


def test_render_embeds_source(tmp_path):
    fitz = pytest.importorskip("fitz")
    from openresume.render import render_pdf

    out = tmp_path / "resume.pdf"
    render_pdf(xml_to_dict(EX_XML), str(out),
               embed=("resume.xml", EX_XML.read_bytes()))
    doc = fitz.open(str(out))
    assert doc.page_count >= 1
    assert "resume.xml" in doc.embfile_names()
