# Dataset build notes

Command: python collect_apps.py --limit 9001 --seed 666 --out out

## Selection method
- Flathub: deterministic sort by `downloads` then app id; keep top records.
- Arch: query package search for predefined desktop-related terms; fixed-seed shuffle for reproducible sampling.
- Debian: parse official `Packages.gz` for bookworm/main amd64; fixed-seed shuffle and section filters.
- GitHub upstream: optional enrichment for homepages that point to github.com repositories.

## Scoring summary
- Wayland and X11/XLibre-style scores are heuristic (0-5) based on toolkit and metadata mentions.
- Confidence starts low and increases with number/quality of corroborating evidence across sources.

## Known limitations
- Metadata quality differs between repos; many package descriptions do not explicitly mention display stack.
- GitHub release lookup is limited to avoid rate limits and may miss non-GitHub upstreams.
- XLibre is treated as X11/Xorg-style compatibility proxy due to limited explicit ecosystem metadata.