"""End-to-end tests for the local `openresume serve` web app (no browser)."""
import json
import threading
import urllib.error
import urllib.request

import pytest
from http.server import ThreadingHTTPServer

from openresume.server import _Handler

EXAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<resume xmlns="urn:openresume:2.0" version="2.0">
  <name>Alex Morgan</name>
  <title>Platform Engineer</title>
  <contact><email>you@example.com</email><location>Remote</location></contact>
  <summary>Builds reliable systems.</summary>
</resume>
"""


@pytest.fixture(scope="module")
def base_url():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    host, port = httpd.server_address[:2]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def _post(url, data, fmt):
    req = urllib.request.Request(f"{url}?fmt={fmt}", data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        return r.status, r.headers["Content-Type"], r.read()


def test_index_and_examples(base_url):
    with urllib.request.urlopen(base_url + "/") as r:
        assert r.status == 200
        assert r.headers["Content-Type"].startswith("text/html")
        assert b"OpenResume" in r.read()

    xml = urllib.request.urlopen(base_url + "/example.xml").read()
    assert b"urn:openresume:2.0" in xml

    data = json.loads(urllib.request.urlopen(base_url + "/example.json").read())
    assert data["name"]


def test_validate_ok(base_url):
    status, ctype, body = _post(base_url + "/api/validate", EXAMPLE_XML, "xml")
    assert status == 200 and ctype.startswith("application/json")
    payload = json.loads(body)
    assert payload["ok"] is True and payload["errors"] == []
    assert payload["data"]["name"] == "Alex Morgan"


def test_validate_rejects_bad_xml(base_url):
    bad = b'<resume xmlns="urn:openresume:2.0"><title>no name</title></resume>'
    status, _, body = _post(base_url + "/api/validate", bad, "xml")
    payload = json.loads(body)
    assert status == 200 and payload["ok"] is False and payload["errors"]


def test_render_returns_pdf(base_url):
    status, ctype, body = _post(base_url + "/api/render", EXAMPLE_XML, "xml")
    assert status == 200 and ctype == "application/pdf"
    assert body[:5] == b"%PDF-"


def test_render_rejects_invalid(base_url):
    bad = b'<resume xmlns="urn:openresume:2.0"><title>no name</title></resume>'
    req = urllib.request.Request(
        base_url + "/api/render?fmt=xml", data=bad, method="POST")
    try:
        urllib.request.urlopen(req)
        assert False, "expected HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 422
