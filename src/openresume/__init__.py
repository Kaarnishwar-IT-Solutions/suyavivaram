"""OpenResume - an open, renderer-agnostic resume format (XML <-> JSON -> PDF).

Typical use::

    from openresume import xml_to_dict, render_pdf, to_json_string

    data = xml_to_dict("resume.xml")
    render_pdf(data, "resume.pdf", embed=("resume.xml", open("resume.xml","rb").read()))
"""
from .convert import (
    NS,
    dict_to_xml,
    json_to_xml,
    load_json,
    to_json_string,
    to_xml_string,
    xml_to_dict,
    xml_to_json,
)

__version__ = "2.0.0"

__all__ = [
    "NS",
    "xml_to_dict",
    "dict_to_xml",
    "xml_to_json",
    "json_to_xml",
    "to_xml_string",
    "to_json_string",
    "load_json",
    "__version__",
]
