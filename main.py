from __future__ import annotations

import argparse
import subprocess
import sys
import time

def run_step(cmd: list[str]) -> None:
    print(f"\n==> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full pipeline: collect dataset and build static site data")
    # over 9000! https://knowyourmeme.com/memes/over-9000
    parser.add_argument("--limit", type=int, default=9001, help="Number of merged apps to keep")
    parser.add_argument("--seed", type=int, default=666, help="Deterministic seed")
    parser.add_argument("--out", default="out", help="Output folder for dataset artifacts")
    args = parser.parse_args()

    python = sys.executable
    run_step([python, "collect_apps.py", "--limit", str(args.limit), "--seed", str(args.seed), "--out", args.out])
    time.sleep(3)  # ensure file timestamps are updated
    run_step([python, "scripts/build_site.py"])

    print("\nPipeline complete.")
    print("- Dataset: out/apps.csv, out/apps.json, out/sources.json")
    print("- Site data: docs/data/apps.json, docs/data/summary.json")


if __name__ == "__main__":
    main()
