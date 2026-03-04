const SCORE_LABELS = ['0', '1', '2', '3', '4', '5'];
const SCORE_COLORS = ['#dc3545', '#fd7e14', '#ffc107', '#6c757d', '#0d6efd', '#198754'];

let allApps = [];

function percent(count, total) {
  if (!total) return '0.0%';
  return `${((count / total) * 100).toFixed(1)}%`;
}

function scoreBadge(score) {
  const cls = score >= 4 ? 'text-bg-success' : score >= 2 ? 'text-bg-warning' : 'text-bg-danger';
  return `<span class="badge ${cls} badge-score">${score}</span>`;
}

function makeLegendTable(el, counts, total) {
  const rows = SCORE_LABELS.map((label) => {
    const count = counts[label] || 0;
    return `<tr><td>${label}</td><td>${count}</td><td>${percent(count, total)}</td></tr>`;
  }).join('');
  el.innerHTML = `<thead><tr><th>Score</th><th>Count</th><th>%</th></tr></thead><tbody>${rows}</tbody>`;
}

function makeChart(canvasId, counts, total) {
  const data = SCORE_LABELS.map((label) => counts[label] || 0);
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, {
    type: 'doughnut',
    data: { labels: SCORE_LABELS, datasets: [{ data, backgroundColor: SCORE_COLORS }] },
    options: {
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (context) => `Score ${context.label}: ${context.raw} (${percent(context.raw, total)})`,
          },
        },
      },
    },
  });
}

function renderOverlap(summary) {
  const cards = [
    ['Total apps', summary.total_apps],
    ['Both ≥ 4', summary.overlap.both_gte_4],
    ['Wayland-leaning (W≥4, X≤1)', summary.overlap.wayland_gte_4_xlibre_lte_1],
    ['X11-leaning (X≥4, W≤1)', summary.overlap.xlibre_gte_4_wayland_lte_1],
  ];
  const html = cards
    .map(
      ([title, value]) => `<div class="col-6 col-lg-3"><div class="card h-100"><div class="card-body py-3"><div class="text-secondary small">${title}</div><div class="h4 mb-0">${value}</div></div></div></div>`,
    )
    .join('');
  document.getElementById('overlapCards').innerHTML = html;
}

function populateFilters(apps) {
  const scoreOptions = ['all', ...SCORE_LABELS].map((v) => `<option value="${v}">${v === 'all' ? 'All' : v}</option>`).join('');
  document.getElementById('waylandFilter').innerHTML = scoreOptions;
  document.getElementById('xlibreFilter').innerHTML = scoreOptions;

  const toolkits = [...new Set(apps.map((a) => a.toolkit_guess || 'unknown'))].sort();
  document.getElementById('toolkitFilter').innerHTML = ['all', ...toolkits]
    .map((v) => `<option value="${v}">${v === 'all' ? 'All' : v}</option>`)
    .join('');
}

function rowHtml(app, idx) {
  const conf = app.confidence == null ? '' : Number(app.confidence).toFixed(2);
  return `<tr>
    <td>${app.name}</td>
    <td>${app.category || 'unknown'}</td>
    <td>${app.display_version || ''}</td>
    <td>${scoreBadge(app.wayland_score)}</td>
    <td>${scoreBadge(app.xlibre_score)}</td>
    <td>${conf}</td>
    <td><button class="btn btn-sm btn-outline-primary" data-evidence-index="${idx}">View</button></td>
  </tr>`;
}

function renderTable(apps) {
  const tbody = document.querySelector('#appsTable tbody');
  tbody.innerHTML = apps.map((a, idx) => rowHtml(a, idx)).join('');
  document.getElementById('resultCount').textContent = `Showing ${apps.length} of ${allApps.length} apps.`;
  tbody.querySelectorAll('button[data-evidence-index]').forEach((btn) => {
    btn.addEventListener('click', () => openEvidence(apps[Number(btn.getAttribute('data-evidence-index'))]));
  });
}

function openEvidence(app) {
  document.getElementById('evidenceModalTitle').textContent = `Evidence: ${app.name}`;
  const wayland = (app.evidence_wayland || []).map((e) => `<li>${e}</li>`).join('') || '<li>None</li>';
  const xlibre = (app.evidence_xlibre || []).map((e) => `<li>${e}</li>`).join('') || '<li>None</li>';
  const links = [
    app.homepage ? `<li><a href="${app.homepage}" target="_blank" rel="noopener">Homepage</a></li>` : '',
    app.upstream_repo ? `<li><a href="${app.upstream_repo}" target="_blank" rel="noopener">Upstream repo</a></li>` : '',
  ]
    .filter(Boolean)
    .join('');

  document.getElementById('evidenceModalBody').innerHTML = `
    <p class="mb-2"><strong>Notes:</strong> ${app.notes || '—'}</p>
    <div class="row g-3">
      <div class="col-md-6"><h6>Wayland evidence</h6><ul>${wayland}</ul></div>
      <div class="col-md-6"><h6>XLibre/X11 evidence</h6><ul>${xlibre}</ul></div>
    </div>
    <h6>Links</h6><ul>${links || '<li>None</li>'}</ul>
    <p><strong>Sources:</strong> ${(app.sources_used || []).join(', ') || 'None'}</p>
  `;
  new bootstrap.Modal(document.getElementById('evidenceModal')).show();
}

function applyFilters() {
  const query = document.getElementById('searchInput').value.trim().toLowerCase();
  const wf = document.getElementById('waylandFilter').value;
  const xf = document.getElementById('xlibreFilter').value;
  const tf = document.getElementById('toolkitFilter').value;

  const filtered = allApps.filter((a) => {
    const haystack = `${a.name || ''} ${a.category || ''}`.toLowerCase();
    if (query && !haystack.includes(query)) return false;
    if (wf !== 'all' && String(a.wayland_score) !== wf) return false;
    if (xf !== 'all' && String(a.xlibre_score) !== xf) return false;
    if (tf !== 'all' && (a.toolkit_guess || 'unknown') !== tf) return false;
    return true;
  });

  renderTable(filtered);
}

function bindFilters() {
  ['searchInput', 'waylandFilter', 'xlibreFilter', 'toolkitFilter'].forEach((id) => {
    const el = document.getElementById(id);
    el.addEventListener('input', applyFilters);
    el.addEventListener('change', applyFilters);
  });
}

function showLoadError(err) {
  const msg = `Failed to load static JSON files. Use a static server (e.g. python -m http.server) instead of opening file:// directly. Details: ${err}`;
  const box = document.getElementById('loadError');
  box.textContent = msg;
  box.classList.remove('d-none');
  document.getElementById('datasetMeta').textContent = 'Dataset unavailable';
}

async function init() {
  try {
    const [appsResp, summaryResp] = await Promise.all([fetch('data/apps.json'), fetch('data/summary.json')]);
    if (!appsResp.ok || !summaryResp.ok) {
      throw new Error(`HTTP ${appsResp.status}/${summaryResp.status}`);
    }
    allApps = await appsResp.json();
    const summary = await summaryResp.json();

    renderOverlap(summary);
    makeChart('waylandChart', summary.wayland_score_counts, summary.total_apps);
    makeChart('xlibreChart', summary.xlibre_score_counts, summary.total_apps);
    makeLegendTable(document.getElementById('waylandLegend'), summary.wayland_score_counts, summary.total_apps);
    makeLegendTable(document.getElementById('xlibreLegend'), summary.xlibre_score_counts, summary.total_apps);

    populateFilters(allApps);
    renderTable(allApps);
    bindFilters();

    document.getElementById('datasetMeta').textContent = `Apps: ${summary.total_apps} | Generated: ${summary.site_generated_at_utc}`;
    document.getElementById('generatedAt').textContent = `Dataset CSV mtime (UTC): ${summary.source_csv_mtime_utc}. Site generated at (UTC): ${summary.site_generated_at_utc}.`;
  } catch (err) {
    console.error(err);
    showLoadError(err);
  }
}

init();
