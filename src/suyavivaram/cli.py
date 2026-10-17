"""Command-line interface: validate | convert | render."""
import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .convert import (
    load_json, to_json_string, to_xml_string, xml_to_dict, xml_to_json, json_to_xml,
)
from .render import render_pdf
from .validate import validate_json, validate_xml

_HERE = Path(__file__).resolve().parent
_DATA = _HERE / "data"
DEFAULT_XSD = _DATA / "resume.xsd"
DEFAULT_JSON_SCHEMA = _DATA / "resume.schema.json"
DEFAULT_EXAMPLE_XML = _DATA / "example.resume.xml"


def _is_json(path):
    return str(path).lower().endswith(".json")


def cmd_validate(args):
    src = args.file
    if _is_json(src):
        ok, errors = validate_json(load_json(src), args.schema or DEFAULT_JSON_SCHEMA)
        label = "JSON Schema"
    else:
        ok, errors = validate_xml(src, args.xsd or DEFAULT_XSD)
        label = "XSD"
    if ok:
        print(f"OK: {src} is valid against {label}")
        return 0
    print(f"INVALID: {src}", file=sys.stderr)
    for err in errors:
        print(f"  {err}", file=sys.stderr)
    return 2


def cmd_convert(args):
    src, out = args.input, args.output
    if _is_json(out):
        if _is_json(src):
            print("error: input and output are both JSON", file=sys.stderr)
            return 1
        text = xml_to_json(src)
    else:
        if not _is_json(src):
            print("error: input and output are both XML", file=sys.stderr)
            return 1
        text = json_to_xml(src)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {out}")
    return 0


def cmd_render(args):
    src = args.input
    if _is_json(src):
        data = load_json(src)
    else:
        data = xml_to_dict(src)
    embed = None
    if not args.no_embed:
        if _is_json(src):
            embed = ("resume.json", json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        else:
            with open(src, "rb") as fh:
                embed = ("resume.xml", fh.read())
    render_pdf(data, args.output, embed=embed)
    print(f"wrote {args.output}")
    return 0


def cmd_serve(args):
    from .server import serve

    serve(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def _write_model(data, out):
    text = to_xml_string(data) if not _is_json(out) else to_json_string(data)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {out}")
    return 0


def cmd_from_jsonresume(args):
    from .interop import from_jsonresume

    return _write_model(from_jsonresume(args.input), args.output)


def cmd_to_jsonresume(args):
    from .interop import to_jsonresume_string

    src = args.input
    data = load_json(src) if _is_json(src) else xml_to_dict(src)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(to_jsonresume_string(data))
    print(f"wrote {args.output}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="suyavivaram", description="Suyavivaram toolkit")
    p.add_argument("--version", action="version", version=f"suyavivaram {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate an XML or JSON resume")
    v.add_argument("file")
    v.add_argument("--xsd", default=None)
    v.add_argument("--schema", default=None, help="JSON Schema path")
    v.set_defaults(func=cmd_validate)

    c = sub.add_parser("convert", help="convert XML <-> JSON (direction by output extension)")
    c.add_argument("input")
    c.add_argument("output")
    c.set_defaults(func=cmd_convert)

    r = sub.add_parser("render", help="render XML or JSON resume to PDF")
    r.add_argument("input", nargs="?", default=str(DEFAULT_EXAMPLE_XML))
    r.add_argument("-o", "--output", default="resume.pdf")
    r.add_argument("--no-embed", action="store_true", help="do not attach the source to the PDF")
    r.set_defaults(func=cmd_render)

    s = sub.add_parser("serve", help="run the local validate + render web UI")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    s.set_defaults(func=cmd_serve)

    ij = sub.add_parser("from-jsonresume", help="import a JSON Resume (resume.json) into Suyavivaram")
    ij.add_argument("input", help="a JSON Resume file")
    ij.add_argument("-o", "--output", default="resume.xml", help="output .xml or .json")
    ij.set_defaults(func=cmd_from_jsonresume)

    tj = sub.add_parser("to-jsonresume", help="export an Suyavivaram document to JSON Resume")
    tj.add_argument("input", help="an Suyavivaram .xml or .json file")
    tj.add_argument("-o", "--output", default="resume.json", help="output JSON Resume file")
    tj.set_defaults(func=cmd_to_jsonresume)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
