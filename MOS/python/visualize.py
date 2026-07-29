"""
TATIANA — visual debugger for the evolving complex.

Renders a sequence of snapshots of the coarse complex K (modules as vertices,
bound coalitions as edges) into ONE self-contained HTML file you can open in a
browser and step through. No internet, no CDN, no dependencies beyond numpy.

WHY THIS EXISTS
---------------
rho, b0 and omega_e are numbers, and numbers hide structure. When the topology
is mutating (bind / collapse / split / merge) you need to SEE which coalitions
formed, which pair is fighting, and whether the complex has fragmented. A
disconnected complex reporting rho=0 looks fine as a number and is obviously
broken as a picture.

WHAT YOU SEE
------------
  * vertices  = modules; grey ring = the module's own position
  * edges     = bound pairs; THICKER + REDDER = more disagreement (omega_e)
  * dashed red = the worst edge (where RESOLVE should be aimed)
  * components are tinted differently when b0 > 1 (fragmentation is visible)
  * rho / confidence / b0 / status shown per snapshot, with UNKNOWN honestly
    displayed as UNKNOWN rather than as a number

USAGE
-----
    from visualize import Snapshot, render
    snaps = [Snapshot("t=0", states0, edges0), Snapshot("t=1", states1, edges1)]
    render(snaps, "complex.html")
"""

from __future__ import annotations

import html
import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from coherence import coherence, CoherenceReport

Vertex = str
Edge = Tuple[Vertex, Vertex]


@dataclass
class Snapshot:
    """One frame in the life of the complex."""
    label: str
    states: Dict[Vertex, np.ndarray]
    edges: Sequence[Edge]
    note: str = ""

    def report(self) -> CoherenceReport:
        return coherence(self.states, self.edges)


def _components(vertices: Sequence[Vertex], edges: Sequence[Edge]) -> Dict[Vertex, int]:
    """Map each vertex to a component index, so fragmentation is visible."""
    parent = {v: v for v in vertices}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for u, v in edges:
        if u in parent and v in parent:
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
    roots = {}
    out = {}
    for v in vertices:
        r = find(v)
        if r not in roots:
            roots[r] = len(roots)
        out[v] = roots[r]
    return out


def _frame_payload(snap: Snapshot) -> dict:
    rep = snap.report()
    verts = list(snap.states.keys())
    comp = _components(verts, [e for e in snap.edges if e[0] in snap.states and e[1] in snap.states])

    # Circular layout: stable and dependency-free.
    n = max(len(verts), 1)
    pos = {}
    for i, v in enumerate(verts):
        ang = 2.0 * math.pi * i / n - math.pi / 2.0
        pos[v] = (300 + 200 * math.cos(ang), 260 + 200 * math.sin(ang))

    worst = rep.worst_edge()
    max_w = max(rep.per_edge.values()) if rep.per_edge else 0.0

    return {
        "label": snap.label,
        "note": snap.note,
        "rho": rep.rho,
        "confidence": rep.confidence,
        "omega": rep.omega,
        "b0": rep.b0,
        "status": rep.status,
        "n_vertices": rep.n_vertices,
        "n_edges": rep.n_edges,
        "fragmented": rep.is_fragmented,
        "vertices": [{"id": v, "x": pos[v][0], "y": pos[v][1], "comp": comp.get(v, 0)} for v in verts],
        "edges": [
            {
                "u": u, "v": v,
                "x1": pos[u][0], "y1": pos[u][1],
                "x2": pos[v][0], "y2": pos[v][1],
                "w": w,
                "rel": (w / max_w) if max_w > 0 else 0.0,
                "worst": bool(worst is not None and (u, v) == worst),
            }
            for (u, v), w in rep.per_edge.items()
        ],
    }


_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>TATIANA — complex evolution</title>
<style>
 :root{color-scheme:light dark}
 body{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;margin:0;padding:16px;
      background:#0f1115;color:#e6e6e6}
 h1{font-size:15px;margin:0 0 12px;letter-spacing:.5px;color:#9fd0ff}
 .wrap{display:flex;gap:20px;flex-wrap:wrap}
 .panel{background:#171a21;border:1px solid #262b36;border-radius:8px;padding:12px}
 .stat{font-size:13px;line-height:1.9}
 .k{color:#7f8a9e}
 .v{color:#e6e6e6;font-weight:600}
 .warn{color:#ff8a80;font-weight:700}
 .ok{color:#8ee68e;font-weight:700}
 .unk{color:#ffd479;font-weight:700}
 button{background:#232936;color:#e6e6e6;border:1px solid #333b4a;border-radius:6px;
        padding:6px 12px;cursor:pointer;font-family:inherit}
 button:hover{background:#2c3444}
 table{border-collapse:collapse;font-size:12px;margin-top:8px}
 td,th{border:1px solid #2a303c;padding:3px 8px;text-align:left}
 th{color:#7f8a9e;font-weight:600}
 #note{color:#9aa4b5;font-size:12px;margin-top:8px;max-width:520px}
</style></head><body>
<h1>TATIANA — coarse complex K, evolving</h1>
<div class="wrap">
  <div class="panel">
    <svg id="svg" width="600" height="520"></svg>
    <div style="margin-top:8px">
      <button onclick="step(-1)">&#8592; prev</button>
      <button onclick="step(1)">next &#8594;</button>
      <span id="pos" style="margin-left:10px;color:#7f8a9e"></span>
    </div>
  </div>
  <div class="panel stat" style="min-width:300px">
    <div id="stats"></div>
    <div id="edges"></div>
    <div id="note"></div>
  </div>
</div>
<script>
const FRAMES = __FRAMES__;
let i = 0;
const COMP_COLORS = ["#4a90d9","#d98c4a","#8e6fd9","#4ad9a5","#d94a7a","#b5d94a"];

function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

function draw(){
  const f = FRAMES[i];
  let svg = "";
  for(const e of f.edges){
    const t = e.rel;
    const col = e.worst ? "#ff5252" : `rgb(${Math.round(90+165*t)},${Math.round(150-90*t)},${Math.round(190-120*t)})`;
    const wdt = 1.5 + 6*t;
    svg += `<line x1="${e.x1}" y1="${e.y1}" x2="${e.x2}" y2="${e.y2}" stroke="${col}"
            stroke-width="${wdt}" ${e.worst?'stroke-dasharray="7,5"':''} opacity="0.9"/>`;
    const mx=(e.x1+e.x2)/2, my=(e.y1+e.y2)/2;
    svg += `<text x="${mx}" y="${my-5}" fill="#8b95a8" font-size="10" text-anchor="middle">${e.w.toFixed(2)}</text>`;
  }
  for(const v of f.vertices){
    const c = COMP_COLORS[v.comp % COMP_COLORS.length];
    svg += `<circle cx="${v.x}" cy="${v.y}" r="26" fill="#1c2129" stroke="${c}" stroke-width="3"/>`;
    svg += `<text x="${v.x}" y="${v.y+4}" fill="#dfe6f0" font-size="11" text-anchor="middle">${esc(v.id)}</text>`;
  }
  document.getElementById("svg").innerHTML = svg;

  const rho = f.rho===null ? '<span class="unk">UNKNOWN</span>' : `<span class="v">${f.rho.toFixed(4)}</span>`;
  const conf = f.confidence===null ? '<span class="unk">UNKNOWN</span>' : `<span class="v">${f.confidence.toFixed(4)}</span>`;
  const frag = f.fragmented ? '<span class="warn">YES — coherence is only LOCAL</span>' : '<span class="ok">no</span>';
  document.getElementById("stats").innerHTML =
     `<div><span class="k">snapshot:</span> <span class="v">${esc(f.label)}</span></div>`
   + `<div><span class="k">rho (discord):</span> ${rho}</div>`
   + `<div><span class="k">confidence:</span> ${conf}</div>`
   + `<div><span class="k">omega (raw):</span> <span class="v">${f.omega.toFixed(4)}</span></div>`
   + `<div><span class="k">b0 (components):</span> <span class="v">${f.b0}</span></div>`
   + `<div><span class="k">fragmented:</span> ${frag}</div>`
   + `<div><span class="k">V / E:</span> <span class="v">${f.n_vertices} / ${f.n_edges}</span></div>`
   + `<div><span class="k">status:</span> <span class="v">${esc(f.status)}</span></div>`;

  let tbl = "";
  if(f.edges.length){
    tbl = '<table><tr><th>edge</th><th>omega_e</th><th></th></tr>';
    const sorted = [...f.edges].sort((a,b)=>b.w-a.w);
    for(const e of sorted){
      tbl += `<tr><td>${esc(e.u)} — ${esc(e.v)}</td><td>${e.w.toFixed(4)}</td>`
           + `<td>${e.worst?'<span class="warn">&#9664; RESOLVE here</span>':''}</td></tr>`;
    }
    tbl += '</table>';
  } else {
    tbl = '<div class="warn" style="margin-top:8px">no edges — nobody is talking, so agreement is meaningless</div>';
  }
  document.getElementById("edges").innerHTML = tbl;
  document.getElementById("note").textContent = f.note || "";
  document.getElementById("pos").textContent = `${i+1} / ${FRAMES.length}`;
}
function step(d){ i = Math.max(0, Math.min(FRAMES.length-1, i+d)); draw(); }
document.addEventListener("keydown", e=>{ if(e.key==="ArrowLeft")step(-1); if(e.key==="ArrowRight")step(1); });
draw();
</script></body></html>
"""


def render(snapshots: Sequence[Snapshot], out_path: str = "complex.html") -> str:
    """Write a self-contained HTML visualisation. Returns the absolute path."""
    frames = [_frame_payload(s) for s in snapshots]
    doc = _TEMPLATE.replace("__FRAMES__", json.dumps(frames))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return os.path.abspath(out_path)


if __name__ == "__main__":
    d = 16
    rng = np.random.default_rng(7)
    base = rng.normal(size=d)
    mods = ["Planner", "Search", "Reason", "Verify", "Memory", "Reflect"]

    def st(**overrides):
        s = {m: base.copy() for m in mods}
        s.update(overrides)
        return s

    snaps = [
        Snapshot("t0 — isolated (no coalitions)", st(), [],
                 "Nobody is bound yet. rho is UNKNOWN, NOT confidence=1: agreement is "
                 "meaningless when no modules are talking. b0=6."),
        Snapshot("t1 — first bind (Search+Reason)", st(),
                 [("Search", "Reason")],
                 "A coalition forms. Still fragmented overall (b0=5)."),
        Snapshot("t2 — triad binds, all agree", st(),
                 [("Search", "Reason"), ("Reason", "Verify"), ("Search", "Verify")],
                 "The derive-and-check triad. rho=0 — perfectly in tune."),
        Snapshot("t3 — Verify DISAGREES", st(Verify=-base),
                 [("Search", "Reason"), ("Reason", "Verify"), ("Search", "Verify")],
                 "Verify contradicts the others. rho spikes; the dashed red edges show "
                 "exactly where RESOLVE should be aimed."),
        Snapshot("t4 — fully connected, resolved", st(),
                 [("Planner", "Search"), ("Search", "Reason"), ("Reason", "Verify"),
                  ("Verify", "Memory"), ("Memory", "Reflect"), ("Reflect", "Planner")],
                 "Conflict resolved and the complex is now connected (b0=1)."),
    ]

    path = render(snaps, os.path.join(os.path.dirname(__file__), "complex.html"))
    print("Wrote visualisation:", path)
    print("Open it in a browser; arrow keys or the buttons step through the evolution.")
    for s in snaps:
        print(f"  {s.label:38s} -> {s.report().summary()}")
