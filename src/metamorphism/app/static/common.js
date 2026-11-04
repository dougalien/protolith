"use strict";

async function api(path, body) {
  const r = await fetch(path, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}),
  });
  return r.json();
}

function connect(onState, onStatus) {
  let es = null, retry = null;
  function open() {
    es = new EventSource("/events");
    es.onmessage = (e) => { onStatus && onStatus(true); onState(JSON.parse(e.data)); };
    es.onerror = () => {
      onStatus && onStatus(false);
      es.close();
      clearTimeout(retry);
      retry = setTimeout(open, 2000);
    };
  }
  open();
}

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v !== null && v !== undefined) e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return e;
}

function setIfIdle(input, value) {
  if (document.activeElement !== input) input.value = value;
}

const SUP = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
  "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻" };
function sup(n) { return String(n).split("").map((c) => SUP[c] || c).join(""); }

function fmtVal(v) {
  if (v === null || v === undefined || !isFinite(v)) return "–";
  const a = Math.abs(v);
  if (a === 0) return "0";
  if (a < 1e-3 || a >= 1e5) {
    const [m, e] = v.toExponential(2).split("e");
    return `${m}×10${sup(parseInt(e, 10))}`;
  }
  return Number(v.toPrecision(3)).toString();
}

// Chemistry as it is printed: the numbers after an element or a bracket as subscripts (Al2SiO5, (OH)2,
// K0.81Na0.19...) and ionic charges as superscripts (Fe3+).  Returns nodes for h() or append().
const CHEM = /([A-Z][a-z]?)(\d?[+-])(?![\w.])|([A-Z][a-z]?|\))(\d+(?:\.\d+)?)/g;
function chem(text) {
  const out = [], str = String(text ?? "");
  let last = 0, m;
  CHEM.lastIndex = 0;
  while ((m = CHEM.exec(str))) {
    const el = m[1] || m[3], num = m[2] || m[4];
    out.push(str.slice(last, m.index) + el);
    out.push(h(m[2] ? "sup" : "sub", {}, num));
    last = m.index + m[0].length;
  }
  out.push(str.slice(last));
  return out.filter((x) => x !== "");
}
// the same for SVG text: tspans shifted down (or up) in a smaller size
function chemSvg(text) {
  const NS = "http://www.w3.org/2000/svg", out = [], str = String(text ?? "");
  let last = 0, m;
  CHEM.lastIndex = 0;
  while ((m = CHEM.exec(str))) {
    const el = m[1] || m[3], num = m[2] || m[4];
    out.push(document.createTextNode(str.slice(last, m.index) + el));
    const t = document.createElementNS(NS, "tspan");
    t.setAttribute("baseline-shift", m[2] ? "super" : "sub"); t.setAttribute("font-size", "75%"); t.textContent = num;
    out.push(t);
    last = m.index + m[0].length;
  }
  out.push(document.createTextNode(str.slice(last)));
  return out;
}
// the text nodes of an element, chemistry formatted in place (for hints and notes written as plain text)
function chemify(el) {
  for (const n of [...el.childNodes]) {
    if (n.nodeType === 3) { const parts = chem(n.data); if (parts.length > 1) n.replaceWith(...parts); }
    else if (n.nodeType === 1 && !["SUB", "SUP", "INPUT", "SELECT", "TEXTAREA", "SCRIPT"].includes(n.tagName)) chemify(n);
  }
  return el;
}
// an assemblage ("Grt Bt Ms Pl Qz H2O") as chips; names: {abbr: full name} for the tooltips
function chips(label, names, cls = "") {
  return h("span", { class: `chips ${cls}` }, ...String(label || "").split(/\s+/).filter(Boolean).map((a) =>
    h("span", { class: a === "H2O" ? "chip fluid" : "chip", title: (names && names[a.replace(/^\d/, "")]) || (a === "H2O" ? "free water" : "") }, ...chem(a))));
}
