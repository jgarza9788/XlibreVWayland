from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(str(value).strip())
    except Exception:
        return default
    return max(0, min(5, parsed))


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _parse_listish(raw: str | None) -> list[str]:
    if raw is None:
        return []
    text = raw.strip()
    if not text:
        return []

    if text.startswith("["):
        try:
            loaded = json.loads(text)
            if isinstance(loaded, list):
                return [str(x).strip() for x in loaded if str(x).strip()]
            if isinstance(loaded, str) and loaded.strip():
                return [loaded.strip()]
        except Exception:
            pass

    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]

    return [text]


def _display_version(row: dict[str, str]) -> str:
    for key in (
        "latest_version_upstream",
        "latest_version_flathub",
        "latest_version_arch",
        "latest_version_debian",
    ):
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _category(row: dict[str, str]) -> str:
    for key in ("category", "type"):
        value = (row.get(key) or "").strip()
        if value:
            return value
    return "unknown"


def normalize(csv_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    toolkit_present = False
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            name = (row.get("name") or row.get("software") or "").strip() or f"app-{idx+1}"
            toolkit = (row.get("toolkit_guess") or "").strip()
            if toolkit:
                toolkit_present = True

            app = {
                "app_id": (row.get("app_id") or name.lower().replace(" ", "-")).strip(),
                "name": name,
                "category": _category(row),
                "display_version": _display_version(row),
                "wayland_score": _parse_int(row.get("wayland_score"), 0),
                "xlibre_score": _parse_int(row.get("xlibre_score"), 0),
                "confidence": _parse_float(row.get("confidence")),
                "toolkit_guess": toolkit or "unknown",
                "homepage": (row.get("homepage") or "").strip() or None,
                "upstream_repo": (row.get("upstream_repo") or "").strip() or None,
                "evidence_wayland": _parse_listish(row.get("evidence_wayland")),
                "evidence_xlibre": _parse_listish(row.get("evidence_xlibre")),
                "sources_used": _parse_listish(row.get("sources_used")),
                "notes": (row.get("notes") or "").strip(),
            }
            apps.append(app)

    apps.sort(key=lambda x: x["name"].lower())

    wayland = {str(i): 0 for i in range(6)}
    xlibre = {str(i): 0 for i in range(6)}
    for app in apps:
        wayland[str(app["wayland_score"])] += 1
        xlibre[str(app["xlibre_score"])] += 1

    summary = {
        "total_apps": len(apps),
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "source_csv": str(csv_path),
        "source_csv_mtime": datetime.fromtimestamp(csv_path.stat().st_mtime, tz=timezone.utc).isoformat(),
        "wayland_score_counts": wayland,
        "xlibre_score_counts": xlibre,
        "toolkit_filter_enabled": toolkit_present,
    }

    return apps, summary


def render_html(apps: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    app_data_json = json.dumps(apps, ensure_ascii=False)
    summary_json = json.dumps(summary, ensure_ascii=False)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>XLibre v Wayland Report</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\" />
  <style>
    body {{ background:#0b1220; color:#e5e7eb; }}
    .bg-panel {{ background:#111827; }}
    .table {{ --bs-table-bg: transparent; --bs-table-color: #e5e7eb; --bs-table-hover-color: #fff; --bs-table-hover-bg: rgba(255,255,255,.05); }}
    .text-secondary {{ color:#9ca3af !important; }}
    a {{ color:#93c5fd; }}
    .card {{ border-radius: .75rem; }}
    .clickable-row {{ cursor:pointer; }}
    .score-badge {{ min-width:2rem; display:inline-block; text-align:center; }}
    footer {{ font-size:.9rem; }}

    .text-bg-score-0 {{ background-color: #dc2626; }}
    .text-bg-score-1 {{ background-color: #fd7e14; }}
    .text-bg-score-2 {{ background-color: #ffc107; }}
    .text-bg-score-3 {{ background-color: #6c757d; }}
    .text-bg-score-4 {{ background-color: #0d6efd; }}
    .text-bg-score-5 {{ background-color: #198754; }}
  </style>
</head>
<body data-bs-theme="dark">
<nav class=\"navbar navbar-expand-lg navbar-dark bg-black border-bottom\">
  <div class=\"container\">
    <a class=\"navbar-brand\" href=\"#\">XLibre v Wayland</a>
    <div class=\"navbar-nav ms-auto\">
      <a class=\"nav-link\" href=\"https://github.com/jgarza9788/XlibreVWayland\" target=\"_blank\" rel=\"noopener\">Repo</a>
      <a class=\"nav-link\" href=\"../out/apps.csv\" target=\"_blank\">CSV</a>
      <a class=\"nav-link\" href=\"../scripts/build_report.py\" target=\"_blank\">Generator</a>
    </div>
  </div>
</nav>

<header class=\"py-4 border-bottom bg-panel\">
  <div class=\"container\">
    <h1 class=\"h3 mb-1\">Linux Display-Stack Compatibility Report</h1>
    <p class=\"mb-1\">Scores are 0–5 where 5 indicates strongest support. XLibre is treated as X11/Xorg-style compatibility.</p>
    <div class=\"small text-secondary\">Total apps: <span id=\"totalApps\"></span> • Generated on: <span id=\"generatedOn\"></span></div>
  </div>
</header>

<main class=\"container py-4\">
  <div class=\"row g-4 mb-4\">
    <div class=\"col-12 col-lg-6\">
      <div class=\"card h-100 bg-panel\"><div class=\"card-body\">
        <h2 class=\"h5\">Wayland score distribution</h2>
        <canvas id=\"waylandChart\" height=\"220\"></canvas>
        <table class=\"table table-sm mt-3\" id=\"waylandLegend\"></table>
      </div></div>
    </div>
    <div class=\"col-12 col-lg-6\">
      <div class=\"card h-100 bg-panel\"><div class=\"card-body\">
        <h2 class=\"h5\">XLibre score distribution</h2>
        <canvas id=\"xlibreChart\" height=\"220\"></canvas>
        <table class=\"table table-sm mt-3\" id=\"xlibreLegend\"></table>
      </div></div>
    </div>
  </div>

  <div class=\"card bg-panel\"><div class=\"card-body\">
    <div class=\"row g-2 mb-3\">
      <div class=\"col-md-4\"><label class=\"form-label\">Search by name</label><input id=\"search\" class=\"form-control\" placeholder=\"Search name/category\"></div>
      <div class=\"col-6 col-md-2\"><label class=\"form-label\">Wayland min</label><select id=\"wMin\" class=\"form-select\"></select></div>
      <div class=\"col-6 col-md-2\"><label class=\"form-label\">Wayland max</label><select id=\"wMax\" class=\"form-select\"></select></div>
      <div class=\"col-6 col-md-2\"><label class=\"form-label\">XLibre min</label><select id=\"xMin\" class=\"form-select\"></select></div>
      <div class=\"col-6 col-md-2\"><label class=\"form-label\">XLibre max</label><select id=\"xMax\" class=\"form-select\"></select></div>
      <div class=\"col-md-4\" id=\"toolkitWrap\"><label class=\"form-label\">Toolkit</label><select id=\"toolkit\" class=\"form-select\"></select></div>
      <div class=\"col-md-2\"><label class=\"form-label\">Rows</label><select id=\"pageSize\" class=\"form-select\"><option>25</option><option selected>50</option><option>100</option></select></div>
    </div>

    <div class=\"table-responsive\">
      <table class=\"table table-hover table-sm\">
        <thead><tr>
          <th data-sort=\"name\" role=\"button\">Name</th>
          <th data-sort=\"category\" role=\"button\">Category</th>
          <th data-sort=\"display_version\" role=\"button\">Display version</th>
          <th data-sort=\"wayland_score\" role=\"button\">Wayland</th>
          <th data-sort=\"xlibre_score\" role=\"button\">XLibre</th>
          <th data-sort=\"confidence\" role=\"button\">Confidence</th>
        </tr></thead>
        <tbody id=\"rows\"></tbody>
      </table>
    </div>
    <div class=\"d-flex justify-content-between align-items-center\">
      <small id=\"resultInfo\" class=\"text-secondary\"></small>
      <div class=\"btn-group\">
        <button id=\"prev\" class=\"btn btn-outline-secondary btn-sm\">Prev</button>
        <button id=\"next\" class=\"btn btn-outline-secondary btn-sm\">Next</button>
      </div>
    </div>
  </div></div>
</main>

<footer class=\"container pb-4 text-secondary\">
  Generated by AI / automated tooling. See <a href=\"../out/apps.csv\">dataset CSV</a> and <a href=\"../scripts/build_report.py\">generator script</a>.
</footer>

<div class=\"modal fade\" id=\"detailModal\" tabindex=\"-1\"><div class=\"modal-dialog modal-lg modal-dialog-scrollable\"><div class=\"modal-content\">
  <div class=\"modal-header\"><h5 class=\"modal-title\" id=\"detailTitle\"></h5><button class=\"btn-close\" data-bs-dismiss=\"modal\"></button></div>
  <div class=\"modal-body\" id=\"detailBody\"></div>
</div></div></div>

<script>window.APP_DATA = {app_data_json}; window.SUMMARY = {summary_json};</script>
<script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js\"></script>
<script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js\"></script>
<script>
const labels = ['0','1','2','3','4','5'];
const colors = ['#dc3545','#fd7e14','#ffc107','#6c757d','#0d6efd','#198754'];
const state = {{ sortKey: 'name', sortDir: 1, page: 1 }};

function pct(n,t) {{ return t ? ((n/t)*100).toFixed(1)+'%' : '0.0%'; }}
//function badge(n) {{ const cls=n>=4?'text-bg-success':(n>=2?'text-bg-warning':'text-bg-danger'); return `<span class="badge ${{cls}} score-badge">${{n}}</span>`; }}
function badge(n) {{ 
  let cls = '';
  switch (n) {{
    case 0: cls = 'text-bg-score-0'; break;
    case 1: cls = 'text-bg-score-1'; break;
    case 2: cls = 'text-bg-score-2'; break;
    case 3: cls = 'text-bg-score-3'; break;
    case 4: cls = 'text-bg-score-4'; break;
    case 5: cls = 'text-bg-score-5'; break;
  }}
  return `<span class="badge ${{cls}} score-badge">${{n}}</span>`; 
}}
function makeLegend(elId, counts, total) {{
  const rows = labels.map(l => `<tr><td>${{l}}</td><td>${{counts[l]||0}}</td><td>${{pct(counts[l]||0,total)}}</td></tr>`).join('');
  document.getElementById(elId).innerHTML = `<thead><tr><th>Score</th><th>Count</th><th>%</th></tr></thead><tbody>${{rows}}</tbody>`;
}}
function makeChart(canvasId, counts, total) {{
  new Chart(document.getElementById(canvasId), {{ type:'doughnut', data: {{ labels, datasets:[{{ data: labels.map(l=>counts[l]||0), backgroundColor: colors }}] }}, options:{{ plugins:{{ tooltip:{{ callbacks:{{ label:(ctx)=>`Score ${{ctx.label}}: ${{ctx.raw}} (${{pct(ctx.raw,total)}})` }} }}, legend:{{position:'bottom'}} }} }} }});
}}

function setupFilters() {{
  const scoreOptions = ['0','1','2','3','4','5'].map(v=>`<option value="${{v}}">${{v}}</option>`).join('');
  ['wMin','xMin'].forEach(id => document.getElementById(id).innerHTML = scoreOptions.replace('value="0"','value="0" selected'));
  ['wMax','xMax'].forEach(id => document.getElementById(id).innerHTML = scoreOptions.replace('value="5"','value="5" selected'));

  const toolkit = document.getElementById('toolkit');
  if (!window.SUMMARY.toolkit_filter_enabled) {{
    document.getElementById('toolkitWrap').classList.add('d-none');
  }} else {{
    const values = [...new Set(window.APP_DATA.map(a => a.toolkit_guess || 'unknown'))].sort();
    toolkit.innerHTML = ['all', ...values].map(v=>`<option value="${{v}}">${{v==='all'?'All':v}}</option>`).join('');
  }}
}}

function filtered() {{
  const q = document.getElementById('search').value.toLowerCase().trim();
  const wMin = Number(document.getElementById('wMin').value);
  const wMax = Number(document.getElementById('wMax').value);
  const xMin = Number(document.getElementById('xMin').value);
  const xMax = Number(document.getElementById('xMax').value);
  const toolkitEl = document.getElementById('toolkit');
  const toolkit = toolkitEl ? toolkitEl.value : 'all';

  return window.APP_DATA.filter(a => {{
    const hay = `${{a.name||''}} ${{a.category||''}}`.toLowerCase();
    if (q && !hay.includes(q)) return false;
    if (a.wayland_score < wMin || a.wayland_score > wMax) return false;
    if (a.xlibre_score < xMin || a.xlibre_score > xMax) return false;
    if (toolkit !== 'all' && (a.toolkit_guess||'unknown') !== toolkit) return false;
    return true;
  }});
}}

function sortedRows(data) {{
  const k = state.sortKey, d = state.sortDir;
  return [...data].sort((a,b)=>{{
    const av = a[k] ?? '', bv = b[k] ?? '';
    if (typeof av === 'number' || typeof bv === 'number') return (Number(av)-Number(bv))*d;
    return String(av).localeCompare(String(bv))*d;
  }});
}}

function openDetail(app) {{
  document.getElementById('detailTitle').textContent = app.name;
  const renderList = (items) => (items && items.length) ? `<ul>${{items.map(i=>`<li>${{i}}</li>`).join('')}}</ul>` : '<p class="text-secondary">None</p>';
  const links = [app.homepage ? `<li><a href="${{app.homepage}}" target="_blank" rel="noopener">Homepage</a></li>` : '', app.upstream_repo ? `<li><a href="${{app.upstream_repo}}" target="_blank" rel="noopener">Upstream repo</a></li>` : ''].join('');
  document.getElementById('detailBody').innerHTML = `
    <p><strong>Category:</strong> ${{app.category || 'unknown'}}</p>
    <p><strong>Version:</strong> ${{app.display_version || '—'}}</p>
    <p><strong>Notes:</strong> ${{app.notes || '—'}}</p>
    <h6>Links</h6>${{links?`<ul>${{links}}</ul>`:'<p class="text-secondary">None</p>'}}
    <h6>Wayland evidence</h6>${{renderList(app.evidence_wayland)}}
    <h6>XLibre evidence</h6>${{renderList(app.evidence_xlibre)}}
    <h6>Sources used</h6>${{renderList(app.sources_used)}}`;
  new bootstrap.Modal(document.getElementById('detailModal')).show();
}}

function render() {{
  const data = sortedRows(filtered());
  const pageSize = Number(document.getElementById('pageSize').value);
  const pages = Math.max(1, Math.ceil(data.length / pageSize));
  if (state.page > pages) state.page = pages;
  const start = (state.page - 1) * pageSize;
  const pageRows = data.slice(start, start + pageSize);

  const body = document.getElementById('rows');
  body.innerHTML = pageRows.map((a,idx)=>`<tr class="clickable-row" data-idx="${{start+idx}}"><td>${{a.name}}</td><td>${{a.category||'unknown'}}</td><td>${{a.display_version||''}}</td><td>${{badge(a.wayland_score)}}</td><td>${{badge(a.xlibre_score)}}</td><td>${{a.confidence==null?'':Number(a.confidence).toFixed(2)}}</td></tr>`).join('');
  body.querySelectorAll('tr').forEach(tr => tr.addEventListener('click', () => openDetail(data[Number(tr.dataset.idx)])));

  document.getElementById('resultInfo').textContent = `Showing ${{pageRows.length}} of ${{data.length}} filtered apps (page ${{state.page}}/${{pages}})`;
  document.getElementById('prev').disabled = state.page <= 1;
  document.getElementById('next').disabled = state.page >= pages;
}}

function init() {{
  document.getElementById('totalApps').textContent = window.SUMMARY.total_apps;
  document.getElementById('generatedOn').textContent = window.SUMMARY.generated_on;
  makeChart('waylandChart', window.SUMMARY.wayland_score_counts, window.SUMMARY.total_apps);
  makeChart('xlibreChart', window.SUMMARY.xlibre_score_counts, window.SUMMARY.total_apps);
  makeLegend('waylandLegend', window.SUMMARY.wayland_score_counts, window.SUMMARY.total_apps);
  makeLegend('xlibreLegend', window.SUMMARY.xlibre_score_counts, window.SUMMARY.total_apps);
  setupFilters();

  ['search','wMin','wMax','xMin','xMax','toolkit','pageSize'].forEach(id => {{
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', () => {{ state.page = 1; render(); }});
    if (el) el.addEventListener('change', () => {{ state.page = 1; render(); }});
  }});
  document.querySelectorAll('th[data-sort]').forEach(th => th.addEventListener('click', () => {{
    const k = th.dataset.sort;
    if (state.sortKey === k) state.sortDir *= -1; else {{ state.sortKey = k; state.sortDir = 1; }}
    render();
  }}));
  document.getElementById('prev').addEventListener('click', ()=>{{ state.page--; render(); }});
  document.getElementById('next').addEventListener('click', ()=>{{ state.page++; render(); }});

  render();
}}
init();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a single-file static HTML report from apps.csv")
    parser.add_argument("--csv", default="out/apps.csv", help="Input CSV path")
    parser.add_argument("--out", default="docs/index.html", help="Output HTML path")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out)
    if not csv_path.exists():
        raise SystemExit(f"Missing input csv: {csv_path}")

    apps, summary = normalize(csv_path)
    html = render_html(apps, summary)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} with {len(apps)} apps")


if __name__ == "__main__":
    main()
