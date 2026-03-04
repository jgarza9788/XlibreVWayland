# Files not used by `main.py`

`main.py` directly runs:

- `collect_apps.py`
- `scripts/build_site.py` (which calls `build_site.py`)

The files below are **not directly executed by `main.py`**:

- `scripts/build_report.py`
- `docs/index.html`
- `docs/assets/app.css`
- `docs/assets/app.js`
- `docs/data/apps.json`
- `docs/data/summary.json`
- `tests/test_scoring.py`
- `tests/test_build_site.py`
- `tests/test_build_report.py`
- `ReadMe.md`
- `UNUSED_BY_MAIN.md`
- `LICENSE`
- `requirements.txt`
- `out/README.md`
- `out/apps.csv`
- `out/apps.json`
- `out/sources.json`

Notes:

- Some files above are generated artifacts or test files.
- Dependency modules (for example `models.py`, `http_utils.py`, `scoring.py`, and files in `sources/`) are used indirectly by `main.py` through `collect_apps.py` and are therefore not listed here.
