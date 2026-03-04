# XLibre v Wayland

A reproducible dataset + static reporting project that scores Linux desktop software compatibility for:

- **Wayland** (0–5)
- **XLibre** as an **X11/Xorg-style compatibility proxy** (0–5)

---

## What this repo does

1. Collects application metadata from multiple sources (`collect_apps.py`).
2. Merges and scores apps with explainable evidence.
3. Produces machine-readable dataset artifacts in `out/`.
4. Produces static-site payloads in `docs/data/`.
5. Produces a single-file static report (`docs/index.html`).

---

## Quick start

### Run the main pipeline

```bash
python main.py --limit 500 --seed 123 --out out
```

`main.py` runs:

1. `collect_apps.py`
2. `scripts/build_site.py` (wrapper around `build_site.py`)

---

## Manual commands

### 1) Regenerate dataset

```bash
python collect_apps.py --limit 500 --seed 123 --out out/
```

Outputs:

- `out/apps.csv`
- `out/apps.json`
- `out/sources.json`
- `out/README.md`

### 2) Build static site data

```bash
python scripts/build_site.py
```

Outputs:

- `docs/data/apps.json`
- `docs/data/summary.json`

### 3) Build single-file static HTML report

```bash
python scripts/build_report.py --csv out/apps.csv --out docs/index.html
```

Output:

- `docs/index.html` (embedded dataset + summary, dark mode)

### 4) Preview locally

```bash
cd docs
python -m http.server 8000
# open http://localhost:8000
```

---

## Dark mode

The generated `docs/index.html` report is configured for dark mode styling and uses Bootstrap 5 + Chart.js via CDN.

---

## Tests

```bash
python -m pytest -q
```

---

## Files not used by `main.py`

See:

- `UNUSED_BY_MAIN.md`

This list tracks files that are not directly executed by `main.py`'s pipeline.
