"use strict";
// Metamorphism's control window: a rock, a phase set, water, and one point or a T-P grid.

const $ = (id) => document.getElementById(id);
let INFO = null;
let SYSTEM = "metapelite", WATER = "excess", KIND = "path", PART = "whole";
let SAMPLE = null;          // {summary, parts} of an opened sample

const SYSTEM_HINT = {
  metapelite: "For mudstones and other Al-rich rocks: garnet with spessartine, staurolite, chloritoid, cordierite, biotite, muscovite and paragonite, chlorite, the Al2SiO5 polymorphs and melt.",
  igneous: "For basalts and other mafic or igneous rocks: Magma's minerals, with hornblende, the pyroxenes, olivine, garnet, the feldspars, spinel and melt. Leaves MnO out.",
};
const WATER_HINT = {
  excess: "A free fluid stays at every point, so hydrous minerals are as stable as they can be.",
  bulk: "Only the rock's own H2O: where hydrous minerals need more, the rock is short of water and drier minerals win.",
};

function seg(id, key, value) {
  document.querySelectorAll(`#${id} button`).forEach((x) => x.classList.toggle("on", x.dataset[key] === value));
}
function setSystem(s) { SYSTEM = s; seg("system", "system", s); $("system-hint").replaceChildren(...chem(SYSTEM_HINT[s])); leftOut(); }
function setWater(w) { WATER = w; seg("water", "water", w); $("water-hint").replaceChildren(...chem(WATER_HINT[w])); }
function setKind(k) {
  KIND = k; seg("kind", "kind", k);
  $("grid-box").hidden = k !== "grid"; $("point-box").hidden = k !== "point"; $("path-box").hidden = k !== "path";
  estimate();
}
function setPart(p) {
  PART = p; seg("part", "part", p);
  if (SAMPLE && SAMPLE.parts[p]) fillWt(SAMPLE.parts[p]);
}

function openResults() { window.open("/results", "metamorphism-results"); }

function wt() {
  const out = {};
  for (const ox of INFO.oxides) {
    const v = parseFloat($(`ox-${ox}`).value);
    if (isFinite(v) && v > 0) out[ox] = v;
  }
  return out;
}
function total() {
  const s = Object.values(wt()).reduce((a, b) => a + b, 0);
  $("total").textContent = s.toFixed(2);
  leftOut();
}
function leftOut() {
  if (!INFO) return;
  const w = wt(), out = (INFO.left_out[SYSTEM] || []).filter((ox) => w[ox] > 0);
  $("leftout").hidden = !out.length;
  $("leftout").textContent = out.length ? `The ${SYSTEM === "metapelite" ? "metapelite" : "igneous"} set has no place for ${out.join(" and ")}, so ${out.length > 1 ? "they are" : "it is"} left out of the calculation.` : "";
  chemify($("leftout"));
}
function fillWt(w) {
  for (const ox of INFO.oxides) $(`ox-${ox}`).value = w[ox] ? Number(w[ox].toFixed(3)) : "";
  total();
}
function fillPreset(name) {
  if (name === "sample") return;
  SAMPLE = null; $("sample-box").hidden = true;
  const sel = $("preset");
  [...sel.options].forEach((o) => { if (o.value === "sample") o.remove(); });
  if (name === "custom") { $("preset-source").textContent = "Your own composition."; return; }
  const p = INFO.presets[name];
  fillWt(p.wt);
  $("name").value = name;
  $("preset-source").textContent = p.source; chemify($("preset-source"));
}

function grid() {
  const n = (id) => parseFloat($(id).value);
  return { t: [n("t0"), n("t1"), n("ts")], p: [n("p0"), n("p1"), n("ps")] };
}
function count([a, b, s]) { return s > 0 && b >= a ? Math.floor((b - a) / s + 1e-9) + 1 : 0; }
function estimate() {
  if (!INFO) return;
  if (KIND === "path") { pathEstimate(); return; }
  if (KIND !== "grid") return;
  const g = grid(), nt = count(g.t), np = count(g.p), n = nt * np;
  if (!n) { $("estimate").textContent = "Each axis runs from a lower to a higher value with a positive step."; return; }
  const workers = Math.max(1, Math.min(np, INFO.cpus));
  const sec = n * INFO.seconds_per_point / workers;
  const t = sec < 90 ? `${Math.max(10, Math.round(sec / 10) * 10)} seconds` : `${Math.round(sec / 60)} minutes`;
  $("estimate").textContent = n > INFO.max_points
    ? `${nt} × ${np} = ${n} points is more than ${INFO.max_points}. Use a larger step.`
    : `${nt} temperatures × ${np} pressures = ${n} points, about ${t} on ${workers} core${workers > 1 ? "s" : ""}. Start coarse, then narrow in on the part you want.`;
}

const WAY_ROWS = 4;
function wayRows() {
  const names = ["Start", "Then", "Then", "End"];
  for (let k = 0; k < WAY_ROWS; k++) {
    $("way").append(h("div", { class: "grid3", style: "margin-top:6px" }, h("span", { class: "small" }, k === 0 ? "Start" : "Then"),
      h("input", { id: `wt${k}`, type: "number", "aria-label": `${names[k]} temperature`, oninput: estimate }),
      h("input", { id: `wp${k}`, type: "number", step: "any", "aria-label": `${names[k]} pressure`, oninput: estimate })));
  }
}
function way() {
  const out = [];
  for (let k = 0; k < WAY_ROWS; k++) {
    const t = parseFloat($(`wt${k}`).value), p = parseFloat($(`wp${k}`).value);
    if (isFinite(t) && isFinite(p)) out.push([t, p]);
  }
  return out;
}
function setWay(w) { for (let k = 0; k < WAY_ROWS; k++) { $(`wt${k}`).value = w[k] ? w[k][0] : ""; $(`wp${k}`).value = w[k] ? w[k][1] : ""; } }
function pathEstimate() {
  const n = parseInt($("n").value, 10), w = way();
  if (w.length < 2) { $("path-est").textContent = "Give at least a start and an end. Blank rows are skipped."; return; }
  if (!(n >= 2 && n <= 60)) { $("path-est").textContent = "2 to 60 steps."; return; }
  const workers = Math.max(1, Math.min(Math.ceil(n / 2), INFO.cpus));
  const sec = Math.ceil(n / workers) * INFO.seconds_per_point;
  $("path-est").textContent = `${n} points, about ${sec < 90 ? `${Math.max(10, Math.round(sec / 10) * 10)} seconds` : `${Math.round(sec / 60)} minutes`}.`;
}

function inputs() {
  const base = { bulk: wt(), name: $("name").value.trim(), system: SYSTEM, water: WATER, kind: KIND,
    from_sample: !!SAMPLE, part: SAMPLE ? PART : undefined };
  if (KIND === "path") return { ...base, path: way(), n: parseInt($("n").value, 10) };
  if (KIND === "point") return { ...base, t: parseFloat($("t").value), p: parseFloat($("p").value) };
  return { ...base, ...grid() };
}

async function run() {
  $("err").style.display = "none";
  const r = await api("/api/run", inputs());
  if (r.error) { $("err").textContent = r.error; $("err").style.display = ""; return; }
  openResults();
}

function fmtTime(s) { return s < 60 ? `${Math.round(s)} s` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`; }

function show(st) {
  const running = st.status === "running";
  $("run").disabled = running;
  $("open-ps").disabled = running;
  $("stop").style.display = running ? "" : "none";
  const [k, n] = st.progress;
  $("prog").style.display = running ? "" : "none";
  $("prog").max = n || 1; $("prog").value = k;
  const grid = st.run && st.run.kind === "grid", path = st.run && st.run.kind === "path";
  let msg = "";
  if (running && path) msg = `Running: ${k} of ${n} points done (${fmtTime(st.elapsed)}, ${st.workers} at a time)`;
  else if (st.status === "done" && path) msg = `Done in ${fmtTime(st.elapsed)}. The results window has the path.`;
  else if (running) msg = grid ? `Running: ${k} of ${n} pressure rows done (${fmtTime(st.elapsed)}, ${st.workers} at a time)` : `Running: one point (${fmtTime(st.elapsed)})`;
  else if (st.status === "done") msg = grid ? `Done in ${fmtTime(st.elapsed)}: ${st.grid.fields.length} fields. The results window has the diagram.` : `Done: ${st.point.label}. The results window has the minerals.`;
  else if (st.status === "stopped") msg = st.message || "Stopped.";
  $("status").textContent = msg;
  if (st.status === "error") { $("err").textContent = st.message; $("err").style.display = ""; }
}

function applyCard(c) {
  $("preset").value = c.rock; fillPreset(c.rock);
  setSystem(c.system); setWater(c.water); setKind(c.kind);
  if (c.kind === "point") { $("t").value = c.t; $("p").value = c.p; }
  else if (c.kind === "path") { setWay(c.path); $("n").value = c.n; }
  else {
    [$("t0").value, $("t1").value, $("ts").value] = c.t;
    [$("p0").value, $("p1").value, $("ps").value] = c.p;
  }
  estimate();
  document.querySelectorAll(".cards .scard").forEach((x) => x.classList.toggle("on", x.dataset.key === c.key));
}
function cardEl(c) {
  const meta = c.kind === "path" ? `${c.rock} · ${c.path.map(([t, p]) => `${t} °C ${p} kbar`).join(" → ")}`
    : c.kind === "point" ? `${c.rock} · ${c.t} °C, ${c.p} kbar`
    : `${c.rock} · ${c.t[0]} to ${c.t[1]} °C, ${c.p[0]} to ${c.p[1]} kbar`;
  return h("button", { class: "scard", "data-key": c.key, onclick: () => applyCard(c) },
    h("b", {}, c.title), h("span", { class: "blurb" }, ...chem(c.blurb)), h("span", { class: "meta" }, meta));
}

async function readJson(file) {
  const text = await file.text();
  try { return JSON.parse(text); } catch (e) { throw new Error(`${file.name} is not a JSON file`); }
}
async function openSample(file) {
  $("err").style.display = "none";
  try {
    const r = await api("/api/open-sample", await readJson(file));
    if (r.error) throw new Error(r.error);
    SAMPLE = r;
    const s = r.summary, sel = $("preset");
    if (![...sel.options].some((o) => o.value === "sample")) sel.prepend(h("option", { value: "sample" }, "From the sample file"));
    sel.value = "sample";
    $("sample-box").hidden = false;
    const from = [s.app && `from ${s.app}`, s.t_c != null && `at ${Math.round(s.t_c)} °C`].filter(Boolean).join(" ");
    $("sample-what").textContent = `${file.name}${from ? `, ${from}` : ""}${s.phases.length ? `: ${s.phases.join(", ")}` : ""}${s.has_melt ? (s.phases.length ? " and melt" : ": melt") : ""}.`;
    for (const b of document.querySelectorAll("#part button")) b.disabled = !r.parts[b.dataset.part];
    $("preset-source").textContent = "The sample you opened. Samples written from here keep it as their parent.";
    $("name").value = (s.note || file.name.replace(/\.[^.]+$/, "")).slice(0, 80);
    setPart(r.parts[PART] ? PART : Object.keys(r.parts)[0]);
  } catch (e) { $("err").textContent = e.message; $("err").style.display = ""; }
}
async function openPseudosection(file) {
  $("err").style.display = "none";
  try {
    const r = await api("/api/open-pseudosection", await readJson(file));
    if (r.error) throw new Error(r.error);
    openResults();
  } catch (e) { $("err").textContent = e.message; $("err").style.display = ""; }
}

async function init() {
  INFO = await (await fetch("/api/presets")).json();
  const sel = $("preset");
  for (const name of Object.keys(INFO.presets)) sel.append(h("option", { value: name }, name[0].toUpperCase() + name.slice(1)));
  sel.append(h("option", { value: "custom" }, "Your own"));
  sel.addEventListener("change", () => fillPreset(sel.value));
  for (const ox of INFO.oxides) {
    const inp = h("input", { id: `ox-${ox}`, type: "number", min: "0", step: "any", "aria-label": `${ox} wt%`,
      oninput: () => { total(); if (sel.value !== "sample") { sel.value = "custom"; $("preset-source").textContent = "Your own composition."; } } });
    $("oxides").append(h("label", { class: "f" }, h("span", {}, ...chem(ox)), inp));
  }
  document.querySelectorAll("#system button").forEach((b) => b.addEventListener("click", () => setSystem(b.dataset.system)));
  document.querySelectorAll("#water button").forEach((b) => b.addEventListener("click", () => setWater(b.dataset.water)));
  document.querySelectorAll("#kind button").forEach((b) => b.addEventListener("click", () => setKind(b.dataset.kind)));
  document.querySelectorAll("#part button").forEach((b) => b.addEventListener("click", () => setPart(b.dataset.part)));
  wayRows();
  $("n").addEventListener("input", estimate);
  for (const id of ["t0", "t1", "ts", "p0", "p1", "ps"]) $(id).addEventListener("input", estimate);
  $("open-sample").addEventListener("click", () => $("sample-file").click());
  $("sample-file").addEventListener("change", (e) => { if (e.target.files[0]) openSample(e.target.files[0]); e.target.value = ""; });
  $("open-ps").addEventListener("click", () => $("ps-file").click());
  $("ps-file").addEventListener("change", (e) => { if (e.target.files[0]) openPseudosection(e.target.files[0]); e.target.value = ""; });
  $("run").addEventListener("click", run);
  $("stop").addEventListener("click", () => api("/api/stop"));
  $("open-results").addEventListener("click", openResults);
  for (const c of INFO.cards) $(`cards-${c.kind}`).append(cardEl(c));
  applyCard(INFO.cards[0]);
  connect(show, (ok) => { $("pill-link").textContent = ok ? "running" : "not connected"; $("pill-link").className = `pill ${ok ? "ok" : "bad"}`; });
}
init();
