"use strict";
// Metamorphism's results window: the pseudosection (fields, boundaries, labels), shading by variance or by
// a mineral's mode, and the minerals of the cell you click, with Save sample and Send to Reaction.

const $ = (id) => document.getElementById(id);
const SVGNS = "http://www.w3.org/2000/svg";
let ST = null;
let SEL = null;            // {i, j} the selected cell
let HL = null;             // a field id highlighted from the list
let POINT = null;          // the selected point's minerals (from /api/point)
let POINT_KEY = "";
let LAYOUT = null;         // the plot's geometry, for the mouse

function s(tag, attrs, ...kids) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) if (v !== null && v !== undefined) e.setAttribute(k, v);
  for (const k of kids) if (k !== null && k !== undefined) e.append(k.nodeType ? k : document.createTextNode(String(k)));
  return e;
}
function colours() {
  const cs = getComputedStyle(document.documentElement), v = (n) => cs.getPropertyValue(n).trim();
  return { panel: v("--panel"), ink: v("--ink"), muted: v("--muted"), faint: v("--faint"), axis: v("--axis"),
    grid: v("--grid"), slate: v("--slate"), rust: v("--rust"), accent: v("--s1"), bad: v("--bad"), badbg: v("--bad-bg"),
    font: v("--font") };
}
function edges(x) {
  if (x.length === 1) return [x[0] - 0.5, x[0] + 0.5];
  const mid = x.slice(1).map((v, k) => (v + x[k]) / 2);
  return [x[0] - (mid[0] - x[0]), ...mid, x[x.length - 1] + (x[x.length - 1] - mid[mid.length - 1])];
}
function ticks(lo, hi, n) {
  const span = hi - lo, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((st) => span / st <= n) || 10 * mag;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6));
  return out;
}
// replaceChildren without the nulls and falses of optional parts
function put(el, ...kids) { el.replaceChildren(...kids.filter((k) => k !== null && k !== undefined && k !== false)); }
const fmt = (v, d = 1) => (v === null || v === undefined || !isFinite(v)) ? "–" : Number(v.toFixed(d)).toString();
function fmtTime(sec) { return sec < 60 ? `${Math.round(sec)} s` : `${Math.floor(sec / 60)} min ${Math.round(sec % 60)} s`; }

// ---- the diagram --------------------------------------------------------------------------------
function draw() {
  const g = ST.grid, wrap = $("plot");
  if (!g) { wrap.replaceChildren(); return; }
  const C = colours();
  const W = Math.max(420, wrap.clientWidth || 760), H = Math.round(Math.min(560, Math.max(320, W * 0.62)));
  const m = { l: 58, r: 14, t: 12, b: 46 };
  const te = edges(g.t_c), pe = edges(g.p_kbar);
  const x = (t) => m.l + (t - te[0]) / (te[te.length - 1] - te[0]) * (W - m.l - m.r);
  const y = (p) => H - m.b - (p - pe[0]) / (pe[pe.length - 1] - pe[0]) * (H - m.t - m.b);
  LAYOUT = { te, pe, x, y, W, H, m };
  const svg = s("svg", { xmlns: SVGNS, viewBox: `0 0 ${W} ${H}`, width: W, height: H, "font-family": C.font, "font-size": 12,
    role: "img", "aria-label": `Pseudosection of ${ST.bulk.name}` });
  svg.append(s("rect", { x: 0, y: 0, width: W, height: H, fill: C.panel }));

  const shade = $("shade").value;
  const fields = new Map(g.fields.map((f) => [f.id, f]));
  const vars = g.fields.map((f) => f.variance), vmin = Math.min(...vars), vmax = Math.max(...vars);
  let mmax = 0;
  if (shade !== "variance") for (const row of g.modes) for (const c of row) if (c && c[shade] > mmax) mmax = c[shade];
  const cells = s("g", { "shape-rendering": "crispEdges" });
  for (let i = 0; i < g.p_kbar.length; i++) {
    for (let j = 0; j < g.t_c.length; j++) {
      const k = g.cells[i][j], r = { x: x(te[j]), y: y(pe[i + 1]), width: x(te[j + 1]) - x(te[j]), height: y(pe[i]) - y(pe[i + 1]) };
      if (k === null) { cells.append(s("rect", { ...r, fill: C.grid })); continue; }
      if (k < 0) { cells.append(s("rect", { ...r, fill: C.badbg })); continue; }
      let op;
      if (shade === "variance") op = vmax > vmin ? 0.08 + 0.5 * (fields.get(k).variance - vmin) / (vmax - vmin) : 0.15;
      else op = mmax > 0 ? 0.9 * ((g.modes[i][j] || {})[shade] || 0) / mmax : 0;
      cells.append(s("rect", { ...r, fill: shade === "variance" ? C.slate : C.accent, "fill-opacity": op.toFixed(3) }));
      if (HL === k) cells.append(s("rect", { ...r, fill: C.rust, "fill-opacity": 0.35 }));
    }
  }
  svg.append(cells);

  // axes and grid ticks
  const ax = s("g", { fill: C.muted, stroke: "none" });
  const tt = ticks(te[0], te[te.length - 1], Math.max(3, Math.floor((W - m.l - m.r) / 70)));
  const pt = ticks(pe[0], pe[pe.length - 1], Math.max(3, Math.floor((H - m.t - m.b) / 50)));
  for (const t of tt) {
    ax.append(s("line", { x1: x(t), x2: x(t), y1: H - m.b, y2: H - m.b + 5, stroke: C.axis }));
    ax.append(s("text", { x: x(t), y: H - m.b + 18, "text-anchor": "middle" }, fmt(t, 0)));
  }
  for (const p of pt) {
    ax.append(s("line", { x1: m.l - 5, x2: m.l, y1: y(p), y2: y(p), stroke: C.axis }));
    ax.append(s("text", { x: m.l - 8, y: y(p) + 4, "text-anchor": "end" }, fmt(p, 1)));
  }
  ax.append(s("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "none", stroke: C.axis }));
  ax.append(s("text", { x: (m.l + W - m.r) / 2, y: H - 8, "text-anchor": "middle", fill: C.ink }, "Temperature (°C)"));
  ax.append(s("text", { x: 14, y: (m.t + H - m.b) / 2, "text-anchor": "middle", fill: C.ink,
    transform: `rotate(-90 14 ${(m.t + H - m.b) / 2})` }, "Pressure (kbar)"));
  svg.append(ax);

  // boundaries between fields
  const b = s("g", { stroke: C.ink, "stroke-width": 1.4, "stroke-linecap": "square", fill: "none" });
  let d = "";
  for (const [[t1, p1], [t2, p2]] of g.boundaries) d += `M${x(t1).toFixed(1)} ${y(p1).toFixed(1)}L${x(t2).toFixed(1)} ${y(p2).toFixed(1)}`;
  if (d) b.append(s("path", { d }));
  svg.append(b);

  // labels: the full assemblage where it fits, the field's number where it does not
  const lab = s("g", { fill: C.ink, stroke: C.panel, "stroke-width": 3, "paint-order": "stroke", "stroke-linejoin": "round",
    "font-size": 11, "text-anchor": "middle" });
  const cw = (W - m.l - m.r) / g.t_c.length, ch = (H - m.t - m.b) / g.p_kbar.length;
  for (const f of g.fields) {
    const j = g.t_c.indexOf(f.centre[0]), i = g.p_kbar.indexOf(f.centre[1]);
    if (i < 0 || j < 0 || g.cells[i][j] !== f.id) continue;
    let a = j, z = j;
    while (a > 0 && g.cells[i][a - 1] === f.id) a--;
    while (z < g.t_c.length - 1 && g.cells[i][z + 1] === f.id) z++;
    const span = (z - a + 1) * cw, cx = x((te[a] + te[z + 1]) / 2), cy = y(g.p_kbar[i]) + 4;
    const text = f.label.replace(/ H2O$/, "");
    if (text.length * 6.4 + 8 < span && ch >= 13) lab.append(s("text", { x: cx, y: cy }, text));
    else if (cw >= 14 && ch >= 12) lab.append(s("text", { x: x(g.t_c[j]), y: cy, "font-size": 10 }, f.id + 1));
  }
  svg.append(lab);

  if (SEL && SEL.i < g.p_kbar.length && SEL.j < g.t_c.length) {
    svg.append(s("rect", { x: x(te[SEL.j]) + 1, y: y(pe[SEL.i + 1]) + 1, width: x(te[SEL.j + 1]) - x(te[SEL.j]) - 2,
      height: y(pe[SEL.i]) - y(pe[SEL.i + 1]) - 2, fill: "none", stroke: C.rust, "stroke-width": 2.5 }));
  }
  svg.addEventListener("mousemove", hover);
  svg.addEventListener("mouseleave", () => { $("tip").style.display = "none"; });
  svg.addEventListener("click", (e) => { const c = cellAt(e); if (c) select(c.i, c.j); });
  wrap.replaceChildren(svg);

  // the shading's key
  if (!g.fields.length) {
    $("scale").replaceChildren(h("span", {}, "The cells fill in as each pressure row finishes."));
  } else if (shade === "variance") {
    $("scale").replaceChildren(...[h("span", {}, vmax > vmin ? `Shaded by variance: lightest F = ${vmin}, darkest F = ${vmax}.` : `Every field has variance F = ${vmin}.`),
      g.failed.length ? h("span", { style: `color:${C.bad}` }, `Pink cells: the solver failed (${g.failed.length}).`) : null].filter(Boolean));
  } else {
    $("scale").replaceChildren(h("span", {}, `${shade}, wt% of the rock:`),
      h("span", { class: "ramp", style: `background:linear-gradient(90deg, transparent, ${C.accent})` }),
      h("span", {}, `0 to ${fmt(mmax, 1)}`));
  }
}

function cellAt(e) {
  if (!LAYOUT || !ST.grid) return null;
  const svg = e.currentTarget, r = svg.getBoundingClientRect();
  const px = (e.clientX - r.left) * LAYOUT.W / r.width, py = (e.clientY - r.top) * LAYOUT.H / r.height;
  const { te, pe, x, y } = LAYOUT;
  let j = -1, i = -1;
  for (let k = 0; k < te.length - 1; k++) if (px >= x(te[k]) && px < x(te[k + 1])) j = k;
  for (let k = 0; k < pe.length - 1; k++) if (py <= y(pe[k]) && py > y(pe[k + 1])) i = k;
  return i < 0 || j < 0 ? null : { i, j };
}
function hover(e) {
  const c = cellAt(e), tip = $("tip");
  if (!c) { tip.style.display = "none"; return; }
  const g = ST.grid, k = g.cells[c.i][c.j];
  const f = k !== null && k >= 0 ? g.fields.find((q) => q.id === k) : null;
  const shade = $("shade").value, mode = shade !== "variance" && g.modes[c.i][c.j] ? g.modes[c.i][c.j][shade] : null;
  put(tip, h("b", {}, `${fmt(g.t_c[c.j], 0)} °C, ${fmt(g.p_kbar[c.i], 2)} kbar`), h("br"),
    k === null ? "still running" : k < 0 ? "the solver failed here" : `${f.id + 1}: ${f.label}  (F = ${f.variance})`,
    mode !== null && mode !== undefined ? h("span", {}, h("br"), `${shade} ${fmt(mode, 1)} wt%`) : null);
  const box = $("ps-panel").getBoundingClientRect();
  tip.style.left = `${e.clientX - box.left + 14}px`; tip.style.top = `${e.clientY - box.top + 14}px`;
  tip.style.display = "block";
}

function fieldList() {
  const g = ST.grid;
  $("nfields").textContent = g.fields.length ? `(${g.fields.length})` : "";
  const items = [...g.fields].sort((a, b) => a.id - b.id).map((f) => h("button", {
    class: HL === f.id ? "on" : "", title: `${f.n} cell${f.n > 1 ? "s" : ""}, near ${fmt(f.centre[0], 0)} °C and ${fmt(f.centre[1], 2)} kbar`,
    onmouseenter: () => { if (HL !== f.id) { HL = f.id; draw(); } },
    onmouseleave: () => { HL = null; draw(); },
    onclick: () => { select(g.p_kbar.indexOf(f.centre[1]), g.t_c.indexOf(f.centre[0])); },
  }, h("span", { class: "num" }, f.id + 1), h("span", {}, f.label), h("span", { class: "var" }, `F ${f.variance}`)));
  $("fields").replaceChildren(...items);
}
function shadeOptions() {
  const sel = $("shade"), want = ["variance", ...(ST.grid ? ST.grid.minerals : [])];
  const key = want.join(",");
  if (sel.dataset.key === key) return;
  const keep = sel.value;
  sel.dataset.key = key;
  sel.replaceChildren(...want.map((w) => h("option", { value: w }, w === "variance" ? "variance (F)" : `mode of ${w}`)));
  sel.value = want.includes(keep) ? keep : "variance";
}

// ---- one point -------------------------------------------------------------------------------------
async function select(i, j) {
  if (i < 0 || j < 0) return;
  SEL = { i, j };
  if (ST.grid) draw();
  await loadPoint();
}
async function loadPoint() {
  if (!SEL) return;
  const key = `${ST.run_id}:${SEL.i}:${SEL.j}`;
  if (key === POINT_KEY && POINT) return;
  const r = await fetch(`/api/point?i=${SEL.i}&j=${SEL.j}`);
  if (!r.ok) { POINT = null; POINT_KEY = ""; showPoint(); return; }
  POINT = await r.json(); POINT_KEY = key;
  showPoint();
}
function numbers(n) { return Object.entries(n || {}).map(([k, v]) => `${k} ${fmt(v, 0)}`).join(", "); }
function showPoint() {
  $("pt").hidden = !POINT; $("pt-empty").hidden = !!POINT;
  if (!POINT) {
    $("pt-empty").textContent = SEL && ST.grid ? "That cell is still running, or the solver failed there." : "Click a cell of the diagram to see the minerals there.";
    return;
  }
  const p = POINT;
  $("pt-label").textContent = p.label;
  put($("pt-facts"), 
    h("span", {}, `${fmt(p.t_c, 0)} °C, ${fmt(p.p_kbar, 2)} kbar`),
    h("span", { title: "F = components - phases + 2 (the phase rule)" }, `variance F = ${p.variance}`),
    p.fluid ? h("span", {}, ST.bulk.water === "excess" ? "with free water (in excess)" : `free water ${fmt(p.fluid.grams, 2)} g per 100 g`) :
      h("span", {}, "no free water"),
    p.converged ? null : h("span", { style: "color:var(--warn)" }, "the solver did not fully converge here"));
  const rows = p.minerals.map((mm) => h("tr", {},
    h("td", { class: "l" }, h("b", {}, mm.abbr)), h("td", { class: "l" }, mm.name), h("td", {}, fmt(mm.mode, 1)),
    h("td", { class: "f" }, mm.formula), h("td", { class: "l" }, numbers(mm.numbers))));
  $("pt-table").replaceChildren(h("tr", {}, h("th", { class: "l" }, "Mineral"), h("th", { class: "l" }, ""),
    h("th", {}, "Mode, wt%"), h("th", { class: "l" }, "Formula"), h("th", { class: "l" }, "")), ...rows);
  $("pt-extra").textContent = p.traces.length ? `Traces (under 0.01 wt%): ${p.traces.join(", ")}.` : "";
}

// ---- the page --------------------------------------------------------------------------------------
function download(name, text, type) {
  const a = h("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
  document.body.append(a); a.click(); a.remove();
}

let lastRun = -1, drawKey = "";
function show(st) {
  ST = st;
  const has = st.status !== "idle" && st.bulk;
  $("empty").style.display = has ? "none" : "";
  $("content").style.display = has ? "flex" : "none";
  const running = st.status === "running";
  $("pill-run").style.display = st.status === "idle" ? "none" : "";
  $("pill-run").textContent = { running: "running", done: "done", stopped: "stopped", error: "error" }[st.status] || "";
  $("pill-run").className = `pill ${{ running: "warn", done: "ok", stopped: "", error: "bad" }[st.status] || ""}`;
  if (!has) return;
  if (st.run_id !== lastRun) { lastRun = st.run_id; SEL = null; HL = null; POINT = null; POINT_KEY = ""; drawKey = ""; }
  const grid = st.run.kind === "grid";
  const b = st.bulk;
  $("title").textContent = `${b.name || "Rock"}: ${grid ? "pseudosection" : "one point"}`;
  const [k, n] = st.progress;
  const where = grid ? `${st.grid.t_c[0]} to ${st.grid.t_c[st.grid.t_c.length - 1]} °C, ${st.grid.p_kbar[0]} to ${st.grid.p_kbar[st.grid.p_kbar.length - 1]} kbar, ${st.grid.t_c.length} × ${st.grid.p_kbar.length} points`
    : `${st.run.t} °C, ${st.run.p} kbar`;
  const status = running ? (grid ? `running: ${k} of ${n} pressure rows (${fmtTime(st.elapsed)})` : `running (${fmtTime(st.elapsed)})`)
    : st.status === "error" ? `error: ${st.message}` : st.status === "stopped" ? (st.message || "stopped")
    : st.message || (st.elapsed ? `done in ${fmtTime(st.elapsed)}` : "done");
  $("meta").textContent = `${b.system_label} · water ${b.water === "excess" ? "in excess" : "from the rock"} · ${where} · ${status}`;
  const lo = Object.entries(b.left_out || {});
  $("leftout").hidden = !lo.length;
  $("leftout").textContent = lo.length ? `Left out (the phase set has no place for them): ${lo.map(([ox, v]) => `${ox} ${fmt(v, 2)} wt%`).join(", ")}.` : "";
  $("prog").style.display = running && grid ? "" : "none";
  $("prog").max = n || 1; $("prog").value = k;
  if (!$("notes").childElementCount) $("notes").replaceChildren(...st.notes.map((t) => h("li", {}, t)));
  $("grid-buttons").hidden = !grid;
  $("dl-ps").disabled = !grid || st.status !== "done";
  $("ps-panel").hidden = !grid;
  $("send-box").hidden = !st.can_send;
  if (grid) {
    shadeOptions();
    const key = `${st.run_id}:${st.progress[0]}:${st.status}`;
    if (key !== drawKey) { drawKey = key; draw(); fieldList(); if (SEL && !POINT) loadPoint(); }
  } else if (st.point) {
    if (!SEL) select(0, 0);
  } else { POINT = null; showPoint(); if (running) $("pt-empty").textContent = "Working out the stable minerals…"; }
}

$("shade").addEventListener("change", draw);
window.addEventListener("resize", () => { if (ST && ST.grid) draw(); });
$("dl-svg").addEventListener("click", () => {
  const svg = $("plot").querySelector("svg");
  if (svg) download(`${(ST.bulk.name || "pseudosection").replace(/[^\w]+/g, "_")}.svg`, new XMLSerializer().serializeToString(svg), "image/svg+xml");
});
$("dl-ps").addEventListener("click", () => {
  const a = h("a", { href: "/api/pseudosection", download: "" });
  document.body.append(a); a.click(); a.remove();
});
$("dl-sample").addEventListener("click", () => {
  if (!SEL) return;
  const a = h("a", { href: `/api/sample?i=${SEL.i}&j=${SEL.j}&fluid=${$("smp-fluid").checked ? 1 : 0}`, download: "" });
  document.body.append(a); a.click(); a.remove();
});
// Inside Protolith: the rock (without its free water) goes onto Reaction's card as minerals, at the grams
// in the box per kg of water, and Reaction's window comes forward.
$("send-sample").addEventListener("click", async () => {
  const g = parseFloat($("send-g").value);
  if (!(g > 0)) { $("send-g").reportValidity(); return; }
  if (!SEL) return;
  const reply = await api("/api/send-sample", { i: SEL.i, j: SEL.j, grams: g });
  if (reply.error) { $("smp-note").textContent = reply.error; return; }
  const lines = [...(reply.problems || []), ...(reply.notes || [])];
  $("smp-note").textContent = lines.length ? `Sent to Reaction: ${lines.join("; ")}.` : "On Reaction's card. Press Run there.";
  if (reply.open) window.open(reply.open, "protolith-reaction");
});
connect(show, (ok) => { $("pill-link").textContent = ok ? "connected" : "not connected"; $("pill-link").className = `pill ${ok ? "ok" : "bad"}`; });
