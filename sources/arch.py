from __future__ import annotations

import random

from models import SourceApp, SourceResult
from sources.base import CollectConfig, SourcePlugin


class ArchSource(SourcePlugin):
    name = "arch"
    QUERIES = ["gtk", "qt", "editor", "browser", "media", "terminal", "kde", "gnome", "game", "xorg", "wayland"]

    def collect(self, client, cfg: CollectConfig) -> SourceResult:
        rng = random.Random(cfg.seed)
        items: list[SourceApp] = []
        seen: set[str] = set()
        for query in self.QUERIES:
            try:
                data = client.get_json("https://archlinux.org/packages/search/json/", params={"q": query})
            except Exception:
                continue
            results = data.get("results", [])
            rng.shuffle(results)
            for pkg in results[:120]:
                pkgname = pkg.get("pkgname")
                if not pkgname or pkgname in seen:
                    continue
                seen.add(pkgname)
                items.append(
                    SourceApp(
                        source=self.name,
                        source_id=pkgname,
                        name=pkgname,
                        category=pkg.get("pkgdesc", "unknown").split(" ")[0] if pkg.get("pkgdesc") else "unknown",
                        homepage=pkg.get("url"),
                        version=pkg.get("pkgver"),
                        summary=pkg.get("pkgdesc"),
                        raw_url=f"https://archlinux.org/packages/{pkg.get('repo','core')}/{pkg.get('arch','x86_64')}/{pkgname}/",
                    )
                )
        return SourceResult(source=self.name, items=items, metadata={"retrieved": len(items)})
