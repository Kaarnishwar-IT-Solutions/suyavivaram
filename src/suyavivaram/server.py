"""Local web UI: validate Suyavivaram XML/JSON and render the exact PDF.

Run with ``suyavivaram serve`` and open http://127.0.0.1:8000. This is the
high-fidelity counterpart to the static GitHub Pages tester: XML is checked
against the real XSD and the PDF is produced by the same renderer as the CLI.
"""
import json
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .convert import load_json, to_json_string, to_xml_string, xml_to_dict
from .render import render_pdf
from .validate import validate_json, validate_xml

_DATA = Path(__file__).resolve().parent / "data"
XSD = _DATA / "resume.xsd"
JSON_SCHEMA = _DATA / "resume.schema.json"
EXAMPLE_XML = _DATA / "example.resume.xml"


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Suyavivaram - validate &amp; preview</title>
<style>
  :root { --navy:#1b2a4a; --blue:#2c5f8a; --rule:#3a7cbd; --zebra:#e8f0f7; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: Calibri, "Segoe UI", system-ui, sans-serif; color:#2d2d2d; background:#f4f6f9; }
  header { background:var(--navy); color:#fff; padding:14px 22px; }
  header h1 { margin:0; font-size:18px; letter-spacing:.3px; }
  header p { margin:3px 0 0; color:#a0c4e8; font-size:12px; }
  .wrap { display:flex; gap:14px; padding:14px 22px; align-items:flex-start; flex-wrap:wrap; }
  .col { background:#fff; border:1px solid #dde3ea; border-radius:8px; padding:12px; flex:1 1 420px; min-width:340px; }
  .col h2 { margin:0 0 8px; font-size:13px; color:var(--blue); text-transform:uppercase; letter-spacing:.4px; }
  textarea { width:100%; height:360px; font-family: Consolas, "Cascadia Mono", monospace; font-size:12px;
             border:1px solid #cdd5df; border-radius:6px; padding:8px; resize:vertical; }
  .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:8px 0; }
  button { background:var(--blue); color:#fff; border:0; border-radius:6px; padding:8px 14px; font-size:13px;
           cursor:pointer; }
  button.ghost { background:#eef3f8; color:var(--blue); }
  button:hover { filter:brightness(1.07); }
  label { font-size:13px; }
  .status { margin-top:8px; font-size:13px; padding:8px 10px; border-radius:6px; display:none; }
  .ok { background:#e6f4ea; color:#1e6b34; display:block; }
  .bad { background:#fdecea; color:#a12622; display:block; }
  .bad ul { margin:6px 0 0 18px; padding:0; }
  iframe { width:100%; height:520px; border:1px solid #cdd5df; border-radius:6px; background:#fff; }
  .muted { color:#6a7480; font-size:12px; }
</style>
</head>
<body>
<header>
  <h1>Suyavivaram</h1>
  <p>Validate XML/JSON against the schema and render the exact PDF &mdash; v__VERSION__</p>
</header>
<div class="wrap">
  <div class="col">
    <h2>Input</h2>
    <div class="row">
      <label><input type="radio" name="fmt" value="xml" checked> XML</label>
      <label><input type="radio" name="fmt" value="json"> JSON</label>
      <button class="ghost" id="loadXml">Load example XML</button>
      <button class="ghost" id="loadJson">Load example JSON</button>
      <input type="file" id="file" accept=".xml,.json">
    </div>
    <textarea id="input" spellcheck="false" placeholder="&lt;resume xmlns=&quot;urn:suyavivaram:2.0&quot;&gt; ..."></textarea>
    <div class="row">
      <button id="validate">Validate</button>
      <button id="render">Render PDF</button>
    </div>
    <div id="status" class="status"></div>
    <p class="muted" id="meta"></p>
  </div>
  <div class="col">
    <h2>Rendered PDF</h2>
    <iframe id="pdf" title="PDF output"></iframe>
  </div>
</div>
<script>
const $ = (id) => document.getElementById(id);
const fmt = () => document.querySelector('input[name=fmt]:checked').value;
function setStatus(ok, msgs) {
  const s = $('status');
  if (ok) { s.className = 'status ok'; s.textContent = msgs; }
  else {
    s.className = 'status bad';
    s.innerHTML = 'Invalid' + (msgs.length ? '<ul>' + msgs.map(m => '<li>' + m + '</li>').join('') + '</ul>' : '');
  }
}
$('loadXml').onclick = async () => {
  document.querySelector('input[value=xml]').checked = true;
  $('input').value = await (await fetch('/example.xml')).text();
};
$('loadJson').onclick = async () => {
  document.querySelector('input[value=json]').checked = true;
  $('input').value = await (await fetch('/example.json')).text();
};
$('file').onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  document.querySelector('input[value=' + (f.name.endsWith('.json') ? 'json' : 'xml') + ']').checked = true;
  $('input').value = await f.text();
};
$('validate').onclick = async () => {
  const r = await fetch('/api/validate?fmt=' + fmt(), { method:'POST', body: $('input').value });
  const j = await r.json();
  setStatus(j.ok, j.errors || []);
  if (j.ok) {
    $('meta').textContent = 'Valid. Sections: ' + Object.keys(j.data || {}).filter(k => k !== 'version').join(', ');
    if (j.xml && fmt() === 'json') $('input').value = j.json;
  }
};
$('render').onclick = async () => {
  const r = await fetch('/api/render?fmt=' + fmt(), { method:'POST', body: $('input').value });
  if (!r.ok) {
    let msg = 'Render failed';
    try { msg = (await r.json()).error || msg; } catch (e) {}
    setStatus(false, [msg]); return;
  }
  const blob = await r.blob();
  $('pdf').src = URL.createObjectURL(blob);
  setStatus(true, 'PDF rendered.');
};
</script>
</body>
</html>
"""


def _analyze(fmt, text):
    """Return (ok, errors, data)."""
    if fmt == "json":
        data = load_json(text)
        ok, errors = validate_json(data, JSON_SCHEMA)
        return ok, errors, data
    raw = text.encode("utf-8")
    ok, errors = validate_xml(raw, XSD)
    data = None
    if ok:
        data = xml_to_dict(raw)
    return ok, errors, data


class _Handler(BaseHTTPRequestHandler):
    server_version = "Suyavivaram/" + __version__

    def log_message(self, *args):  # keep the console quiet
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, "application/json; charset=utf-8",
                   json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8",
                       PAGE.replace("__VERSION__", __version__).encode("utf-8"))
        elif path == "/example.xml":
            self._send(200, "application/xml; charset=utf-8", EXAMPLE_XML.read_bytes())
        elif path == "/example.json":
            body = to_json_string(xml_to_dict(EXAMPLE_XML)).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        fmt = (parse_qs(parsed.query).get("fmt", ["xml"])[0] or "xml").lower()
        if fmt not in ("xml", "json"):
            self._json(400, {"error": "fmt must be xml or json"})
            return
        length = int(self.headers.get("Content-Length", 0))
        text = self.rfile.read(length).decode("utf-8")

        if parsed.path == "/api/validate":
            try:
                ok, errors, data = _analyze(fmt, text)
            except Exception as exc:
                self._json(400, {"ok": False, "errors": [str(exc)]})
                return
            payload = {"ok": ok, "errors": errors, "data": data}
            if ok:
                payload["xml"] = to_xml_string(data)
                payload["json"] = to_json_string(data)
            self._json(200, payload)
        elif parsed.path == "/api/render":
            try:
                ok, errors, data = _analyze(fmt, text)
                if not ok:
                    self._json(422, {"error": "Invalid document",
                                     "errors": errors})
                    return
                name = "resume.json" if fmt == "json" else "resume.xml"
                with tempfile.TemporaryDirectory() as d:
                    out = str(Path(d) / "resume.pdf")
                    render_pdf(data, out, embed=(name, text.encode("utf-8")))
                    pdf = Path(out).read_bytes()
                self._send(200, "application/pdf", pdf)
            except Exception as exc:
                self._json(400, {"error": str(exc)})
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")


def serve(host="127.0.0.1", port=8000, open_browser=True):
    httpd = ThreadingHTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}/"
    print(f"Suyavivaram server running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
