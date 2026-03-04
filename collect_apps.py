from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.progress import track

from http_utils import CachedHttpClient
from models import AppRecord, SourceApp
from scoring import score_from_sources
from sources.arch import ArchSource
from sources.base import CollectConfig
from sources.debian import DebianSource
from sources.flathub import FlathubSource
from sources.github import GitHubSource

console = Console()


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def normalized_key(app: SourceApp) -> str:
    sid = app.source_id.lower()
    return sid if "." not in sid else sid.split(".")[-1]


def choose_category(apps: list[SourceApp]) -> str:
    for a in apps:
        if a.category and a.category != "unknown":
            return a.category
    return "unknown"


def choose_homepage(apps: list[SourceApp]) -> str | None:
    for preferred_source in ["github", "flathub", "arch", "debian"]:
        for app in apps:
            if app.source == preferred_source and app.homepage:
                return str(app.homepage)
    return None


def merge_records(grouped: dict[str, list[SourceApp]], limit: int) -> list[AppRecord]:
    out: list[AppRecord] = []
    for _, apps in grouped.items():
        names = sorted({a.name for a in apps}, key=len)
        primary_name = names[0]
        score = score_from_sources(apps)
        versions = {a.source: a.version for a in apps if a.version}
        rec = AppRecord(
            app_id=slugify(primary_name),
            name=primary_name,
            category=choose_category(apps),
            homepage=choose_homepage(apps),
            upstream_repo=next((str(a.upstream_repo) for a in apps if a.upstream_repo), None),
            latest_version_upstream=versions.get("github"),
            latest_version_flathub=versions.get("flathub"),
            latest_version_arch=versions.get("arch"),
            latest_version_debian=versions.get("debian"),
            wayland_score=score.wayland,
            xlibre_score=score.xlibre,
            confidence=score.confidence,
            evidence_wayland=score.evidence_wayland,
            evidence_xlibre=score.evidence_xlibre,
            toolkit_guess=score.toolkit,
            run_mode_guess=score.run_mode,
            sources_used=sorted({a.source for a in apps}),
            notes=score.notes,
        )
        out.append(rec)
    out.sort(key=lambda r: (-r.confidence, r.app_id))
    return out[:limit]


def write_outputs(records: list[AppRecord], source_dump: dict[str, list[dict]], out_dir: Path, args: argparse.Namespace) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "apps.json"
    csv_path = out_dir / "apps.csv"
    src_path = out_dir / "sources.json"
    readme_path = out_dir / "README.md"

    json_path.write_text(json.dumps([r.model_dump() for r in records], indent=2))

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].model_dump().keys()))
        writer.writeheader()
        for rec in records:
            row = rec.model_dump()
            for k in ["evidence_wayland", "evidence_xlibre", "sources_used"]:
                row[k] = " | ".join(row[k])
            writer.writerow(row)

    src_path.write_text(json.dumps(source_dump, indent=2))

    readme_path.write_text(
        "\n".join(
            [
                "# Dataset build notes",
                "",
                f"Command: python collect_apps.py --limit {args.limit} --seed {args.seed} --out {args.out}",
                "",
                "## Selection method",
                "- Flathub: deterministic sort by `downloads` then app id; keep top records.",
                "- Arch: query package search for predefined desktop-related terms; fixed-seed shuffle for reproducible sampling.",
                "- Debian: parse official `Packages.gz` for bookworm/main amd64; fixed-seed shuffle and section filters.",
                "- GitHub upstream: optional enrichment for homepages that point to github.com repositories.",
                "",
                "## Scoring summary",
                "- Wayland and X11/XLibre-style scores are heuristic (0-5) based on toolkit and metadata mentions.",
                "- Confidence starts low and increases with number/quality of corroborating evidence across sources.",
                "",
                "## Known limitations",
                "- Metadata quality differs between repos; many package descriptions do not explicitly mention display stack.",
                "- GitHub release lookup is limited to avoid rate limits and may miss non-GitHub upstreams.",
                "- XLibre is treated as X11/Xorg-style compatibility proxy due to limited explicit ecosystem metadata.",
            ]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", default="out")
    args = parser.parse_args()

    random.seed(args.seed)
    cfg = CollectConfig(limit=args.limit, seed=args.seed)
    client = CachedHttpClient()

    sources = [FlathubSource(), ArchSource(), DebianSource()]
    all_items: list[SourceApp] = []
    source_dump: dict[str, list[dict]] = {}

    for source in track(sources, description="Collecting sources"):
        result = source.collect(client, cfg)
        all_items.extend(result.items)
        source_dump[source.name] = [x.model_dump(mode="json") for x in result.items]
        console.log(f"{source.name}: {len(result.items)} items")

    gh = GitHubSource()
    gh_result = gh.collect(client, cfg, candidates=all_items)
    all_items.extend(gh_result.items)
    source_dump[gh.name] = [x.model_dump(mode="json") for x in gh_result.items]
    console.log(f"github: {len(gh_result.items)} items")

    grouped: dict[str, list[SourceApp]] = defaultdict(list)
    for item in all_items:
        grouped[normalized_key(item)].append(item)

    records = merge_records(grouped, args.limit)
    if not records:
        raise SystemExit("No records collected")

    write_outputs(records, source_dump, Path(args.out), args)
    console.log(f"Wrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()
