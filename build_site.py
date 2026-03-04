from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CSV_PATH = Path("out/apps.csv")
DOCS_DATA_DIR = Path("docs/data")
APPS_JSON = DOCS_DATA_DIR / "apps.json"
SUMMARY_JSON = DOCS_DATA_DIR / "summary.json"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        iv = int(str(value).strip())
    except Exception:
        return default
    return max(0, min(5, iv))


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    sval = str(value).strip()
    if not sval:
        return default
    try:
        return float(sval)
    except Exception:
        return default


def _parse_evidence(raw: str | None) -> list[str]:
    if not raw:
        return []
    text = raw.strip()
    if not text:
        return []

    # JSON list/string
    if text.startswith("["):
        try:
            loaded = json.loads(text)
            if isinstance(loaded, list):
                return [str(x).strip() for x in loaded if str(x).strip()]
            if isinstance(loaded, str) and loaded.strip():
                return [loaded.strip()]
        except Exception:
            pass

    # Legacy pipe-joined values from CSV export
    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]

    return [text]


def _display_version(row: dict[str, str]) -> str:
    for key in [
        "latest_version_upstream",
        "latest_version_flathub",
        "latest_version_arch",
        "latest_version_debian",
        "version",
    ]:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _category(row: dict[str, str]) -> str:
    for key in ["category", "type"]:
        val = (row.get(key) or "").strip()
        if val:
            return val
    return "unknown"


def load_apps(csv_path: Path) -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            name = (row.get("name") or row.get("software") or "").strip()
            if not name:
                name = f"app-{idx + 1}"

            wayland = _to_int(row.get("wayland_score"), default=0)
            xlibre = _to_int(row.get("xlibre_score"), default=0)
            confidence = _to_float(row.get("confidence"))
            sources = _parse_evidence(row.get("sources_used"))

            app = {
                "id": (row.get("app_id") or name.lower().replace(" ", "-")).strip(),
                "name": name,
                "category": _category(row),
                "display_version": _display_version(row),
                "versions": {
                    "upstream": (row.get("latest_version_upstream") or "").strip() or None,
                    "flathub": (row.get("latest_version_flathub") or "").strip() or None,
                    "arch": (row.get("latest_version_arch") or "").strip() or None,
                    "debian": (row.get("latest_version_debian") or "").strip() or None,
                },
                "wayland_score": wayland,
                "xlibre_score": xlibre,
                "confidence": confidence,
                "toolkit_guess": (row.get("toolkit_guess") or "unknown").strip() or "unknown",
                "run_mode_guess": (row.get("run_mode_guess") or "unknown").strip() or "unknown",
                "homepage": (row.get("homepage") or "").strip() or None,
                "upstream_repo": (row.get("upstream_repo") or "").strip() or None,
                "evidence_wayland": _parse_evidence(row.get("evidence_wayland")),
                "evidence_xlibre": _parse_evidence(row.get("evidence_xlibre")),
                "sources_used": sources,
                "notes": (row.get("notes") or "").strip(),
            }
            apps.append(app)

    apps.sort(key=lambda x: x["name"].lower())
    return apps


def summarize(apps: list[dict[str, Any]], source_csv: Path) -> dict[str, Any]:
    wayland_counts = {str(i): 0 for i in range(6)}
    xlibre_counts = {str(i): 0 for i in range(6)}

    both_ge4 = 0
    wayland_leaning = 0
    x11_leaning = 0

    for app in apps:
        w = _to_int(app.get("wayland_score"), 0)
        x = _to_int(app.get("xlibre_score"), 0)
        wayland_counts[str(w)] += 1
        xlibre_counts[str(x)] += 1

        if w >= 4 and x >= 4:
            both_ge4 += 1
        if w >= 4 and x <= 1:
            wayland_leaning += 1
        if x >= 4 and w <= 1:
            x11_leaning += 1

    generated_at = datetime.now(timezone.utc).isoformat()
    src_mtime = datetime.fromtimestamp(source_csv.stat().st_mtime, tz=timezone.utc).isoformat()

    return {
        "total_apps": len(apps),
        "wayland_score_counts": wayland_counts,
        "xlibre_score_counts": xlibre_counts,
        "overlap": {
            "both_gte_4": both_ge4,
            "wayland_gte_4_xlibre_lte_1": wayland_leaning,
            "xlibre_gte_4_wayland_lte_1": x11_leaning,
        },
        "source_csv": str(source_csv),
        "source_csv_mtime_utc": src_mtime,
        "site_generated_at_utc": generated_at,
    }


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing input CSV: {CSV_PATH}")

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    apps = load_apps(CSV_PATH)
    summary = summarize(apps, CSV_PATH)

    APPS_JSON.write_text(json.dumps(apps, indent=2), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote {len(apps)} apps to {APPS_JSON}")
    print(f"Wrote summary to {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
