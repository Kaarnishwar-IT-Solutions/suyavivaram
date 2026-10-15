/* OpenResume online validator - client side.
 * - converts the XML form to the JSON model (mirrors src/openresume/convert.py)
 * - validates the JSON model against resume.schema.json (a small, targeted
 *   implementation of the JSON Schema subset the spec actually uses)
 * - renders a live preview in the "Modern" theme
 */
"use strict";

const $ = (id) => document.getElementById(id);
const fmt = () => document.querySelector("input[name=fmt]:checked").value;
let SCHEMA = null;

/* ------------------------------------------------------------------ utils */
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
const CONTACT_ORDER = ["location", "email", "phone", "website", "linkedin", "github"];

/* ------------------------------------------------------- XML -> JSON model */
function xmlToData(text) {
  const doc = new DOMParser().parseFromString(text, "application/xml");
  const perr = doc.getElementsByTagName("parsererror")[0];
  if (perr) throw new Error("XML is not well-formed.");
  const root = doc.documentElement;
  if (root.localName !== "resume") throw new Error("Root element must be <resume> (found <" + root.localName + ">).");
  const ns = root.namespaceURI;
  if (ns && ns !== "urn:openresume:2.0") throw new Error("Unexpected namespace '" + ns + "' (expected urn:openresume:2.0).");

  const kids = (el) => Array.from(el.children);
  const find = (el, name) => kids(el).find((c) => c.localName === name) || null;
  const txt = (el) => (el ? (el.textContent || "").trim() : "");

  const data = { version: root.getAttribute("version") || "2.0" };
  data.name = txt(find(root, "name"));

  const title = find(root, "title");
  if (title) data.title = txt(title);

  const c = find(root, "contact");
  if (c) {
    const contact = {};
    for (const f of ["email", "phone", "location", "website", "linkedin", "github"]) {
      const el = find(c, f);
      if (el && txt(el) !== "") contact[f] = txt(el);
    }
    if (Object.keys(contact).length) data.contact = contact;
  }

  const sum = find(root, "summary");
  if (sum) data.summary = txt(sum);

  const comp = find(root, "competencies");
  if (comp) {
    data.competencies = kids(comp).filter((x) => x.localName === "group").map((g) => ({
      name: g.getAttribute("name"),
      skills: kids(g).filter((x) => x.localName === "skill").map(txt),
    }));
  }

  const prj = find(root, "projects");
  if (prj) {
    data.projects = kids(prj).filter((x) => x.localName === "project").map((p) => {
      const proj = { title: txt(find(p, "title")) };
      for (const f of ["company", "role", "duration", "description"]) {
        const el = find(p, f);
        if (el) proj[f] = txt(el);
      }
      const notes = find(p, "notes");
      if (notes) proj.notes = kids(notes).filter((x) => x.localName === "note").map(txt);
      return proj;
    });
  }

  const exp = find(root, "experience");
  if (exp) {
    data.experience = kids(exp).filter((x) => x.localName === "position").map((pos) => {
      const e = { role: txt(find(pos, "role")), company: txt(find(pos, "company")) };
      const per = find(pos, "period");
      if (per) e.period = txt(per);
      return e;
    });
  }

  const edu = find(root, "education");
  if (edu) {
    data.education = kids(edu).filter((x) => x.localName === "degree").map((dg) => {
      const d = { qualification: txt(find(dg, "qualification")) };
      for (const f of ["institution", "period"]) {
        const el = find(dg, f);
        if (el) d[f] = txt(el);
      }
      return d;
    });
  }

  const ad = find(root, "additional");
  if (ad) {
    data.additional = kids(ad).filter((x) => x.localName === "item").map((it) => ({
      label: it.getAttribute("label"), value: txt(it),
    }));
  }
  return data;
}

/* ------------------------------------------------- JSON Schema (subset) --- */
function resolveRef(root, ref) {
  return ref.replace(/^#\//, "").split("/").reduce((o, k) => (o ? o[k] : undefined), root);
}

function validate(root, schema, value, path, errors) {
  if (schema.$ref) return validate(root, resolveRef(root, schema.$ref), value, path, errors);
  const t = schema.type;
  const isObj = (v) => v && typeof v === "object" && !Array.isArray(v);
  const typeOk =
    t === "array" ? Array.isArray(value) :
    t === "object" ? isObj(value) :
    t === "string" ? typeof value === "string" :
    t === "integer" ? Number.isInteger(value) :
    t === "number" ? typeof value === "number" :
    t === "boolean" ? typeof value === "boolean" : true;
  if (!typeOk) { errors.push((path || "<root>") + ": expected " + t); return; }

  if (isObj(value) && (schema.properties || schema.required || schema.additionalProperties === false)) {
    for (const req of schema.required || [])
      if (!(req in value)) errors.push((path || "<root>") + ": missing required property '" + req + "'");
    const props = schema.properties || {};
    for (const k of Object.keys(value)) {
      if (props[k]) validate(root, props[k], value[k], path ? path + "." + k : k, errors);
      else if (schema.additionalProperties === false)
        errors.push((path || "<root>") + ": unexpected property '" + k + "'");
    }
  }

  if (Array.isArray(value)) {
    if (schema.minItems && value.length < schema.minItems)
      errors.push((path || "<root>") + ": expected at least " + schema.minItems + " item(s)");
    if (schema.items) value.forEach((v, i) => validate(root, schema.items, v, path + "[" + i + "]", errors));
  }

  if (t === "string" && typeof value === "string" && schema.minLength && value.length < schema.minLength)
    errors.push((path || "<root>") + ": must not be empty");
}

/* --------------------------------------------------------------- preview -- */
function renderPreview(data) {
  let h = "";
  const contactLine = CONTACT_ORDER
    .filter((f) => data.contact && data.contact[f])
    .map((f) => esc(data.contact[f])).join("&nbsp;&nbsp;|&nbsp;&nbsp;");

  h += '<div class="header"><div class="name">' + esc(data.name) + "</div>";
  if (data.title) h += '<div class="title">' + esc(data.title) + "</div>";
  if (contactLine) h += '<div class="contact">' + contactLine + "</div>";
  h += "</div><div class=\"content\">";

  if (data.summary) {
    h += '<div class="section-title">Professional Summary</div><p class="summary">' + esc(data.summary) + "</p>";
  }

  if (data.competencies && data.competencies.length) {
    h += '<div class="section-title">Core Competencies</div><table class="comp"><tr>';
    data.competencies.forEach((g) => { h += "<th>" + esc(g.name) + "</th>"; });
    h += "</tr>";
    const depth = Math.max.apply(null, data.competencies.map((g) => g.skills.length));
    for (let i = 0; i < depth; i++) {
      h += "<tr>";
      data.competencies.forEach((g) => { h += "<td>" + (i < g.skills.length ? esc(g.skills[i]) : "") + "</td>"; });
      h += "</tr>";
    }
    h += "</table>";
  }

  if (data.projects && data.projects.length) {
    h += '<div class="section-title">Key Projects</div>';
    data.projects.forEach((p) => {
      h += '<div class="project">';
      h += '<div class="p-title">&#9679;&nbsp; ' + esc(p.title) + "</div>";
      const meta = [p.role, p.company].filter(Boolean).join("&nbsp;&nbsp;|&nbsp;&nbsp;");
      const line = meta + (p.duration ? (meta ? "&nbsp;&nbsp;|&nbsp;&nbsp;" : "") + esc(p.duration) : "");
      if (line) h += '<div class="p-role">' + line + "</div>";
      if (p.description) h += '<p class="summary">' + esc(p.description) + "</p>";
      if (p.notes && p.notes.length) {
        h += "<ul>";
        p.notes.forEach((n) => { h += "<li>" + esc(n) + "</li>"; });
        h += "</ul>";
      }
      h += "</div>";
    });
  }

  if (data.experience && data.experience.length) {
    h += '<div class="section-title">Professional Experience</div><table class="exp"><tr>' +
         "<th>Period</th><th>Role</th><th>Organization</th></tr>";
    data.experience.forEach((e) => {
      h += '<tr><td class="period">' + esc(e.period || "") + '</td><td class="role">' + esc(e.role || "") +
           '</td><td class="org">' + esc(e.company || "") + "</td></tr>";
    });
    h += "</table>";
  }

  if (data.education && data.education.length) {
    h += '<div class="section-title">Education</div>';
    data.education.forEach((d) => {
      h += '<p class="edu"><b>' + esc(d.qualification) + "</b>" +
           (d.institution ? ' <span>&mdash; ' + esc(d.institution) + "</span>" : "") +
           (d.period ? ' <span>(' + esc(d.period) + ")</span>" : "") + "</p>";
    });
  }

  if (data.additional && data.additional.length) {
    h += '<div class="section-title">Additional Details</div><ul class="extra">';
    data.additional.forEach((it) => {
      h += "<li><b>" + esc(it.label) + ":</b> <span>" + esc(it.value) + "</span></li>";
    });
    h += "</ul>";
  }

  return h + "</div>";
}

/* ------------------------------------------------------------------- UI --- */
function setStatus(ok, msgs) {
  const s = $("status");
  if (ok) { s.className = "status ok"; s.textContent = msgs; }
  else {
    s.className = "status bad";
    s.innerHTML = "Invalid" + (msgs && msgs.length
      ? "<ul>" + msgs.map((m) => "<li>" + esc(m) + "</li>").join("") + "</ul>" : "");
  }
}

function parseInput() {
  const text = $("input").value;
  if (!text.trim()) throw new Error("Nothing to validate.");
  return fmt() === "json" ? JSON.parse(text) : xmlToData(text);
}

function run() {
  const pv = $("preview");
  try {
    const data = parseInput();
    const errors = [];
    validate(SCHEMA, SCHEMA, data, "", errors);
    if (errors.length) {
      setStatus(false, errors);
      $("meta").textContent = "";
      return;
    }
    pv.innerHTML = renderPreview(data);
    setStatus(true, "Valid against urn:openresume:2.0.");
    $("meta").textContent = "Rendered preview below — use Print / Save as PDF to export.";
  } catch (e) {
    setStatus(false, [e.message]);
  }
}

function loadExample(which) {
  document.querySelector("input[value=" + which + "]").checked = true;
  fetch(which === "json" ? "example.resume.json" : "example.resume.xml")
    .then((r) => r.text()).then((t) => { $("input").value = t; });
}

window.addEventListener("DOMContentLoaded", () => {
  fetch("resume.schema.json").then((r) => r.json()).then((s) => { SCHEMA = s; run(); })
    .catch(() => { setStatus(false, ["Could not load resume.schema.json"]); });

  $("validate").onclick = run;
  $("print").onclick = () => window.print();
  $("loadXml").onclick = () => loadExample("xml");
  $("loadJson").onclick = () => loadExample("json");
  $("file").onchange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    document.querySelector("input[value=" + (f.name.endsWith(".json") ? "json" : "xml") + "]").checked = true;
    const rd = new FileReader();
    rd.onload = () => { $("input").value = rd.result; };
    rd.readAsText(f);
  };
  loadExample("xml");
});
