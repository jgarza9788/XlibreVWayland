from __future__ import annotations

from models import SourceApp, SourceResult
from sources.base import CollectConfig, SourcePlugin


class FlathubSource(SourcePlugin):
    name = "flathub"

    def collect(self, client, cfg: CollectConfig) -> SourceResult:
        items: list[SourceApp] = []
        try:
            apps = client.get_json("https://flathub.org/api/v2/apps")
        except Exception:
            return SourceResult(source=self.name, items=[], metadata={"error": "unavailable"})

        # deterministic ordering by downloads then app id when available
        def _downloads(a):
            return a.get("downloads", 0) or 0

        apps = sorted(apps, key=lambda a: (-_downloads(a), a.get("flatpakAppId", "")))
        for app in apps[: max(cfg.limit, 700)]:
            app_id = app.get("flatpakAppId") or app.get("id")
            if not app_id:
                continue
            name = app.get("name") or app_id.split(".")[-1]
            homepage = app.get("homepage") or app.get("url")
            cat = None
            if app.get("categories"):
                cat = app["categories"][0]
            items.append(
                SourceApp(
                    source=self.name,
                    source_id=app_id,
                    name=name,
                    category=cat,
                    homepage=homepage,
                    version=app.get("currentReleaseVersion"),
                    summary=app.get("summary"),
                    raw_url=f"https://flathub.org/apps/{app_id}",
                    popularity=float(_downloads(app)),
                )
            )
        return SourceResult(source=self.name, items=items, metadata={"retrieved": len(items)})
