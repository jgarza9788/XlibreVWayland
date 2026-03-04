from __future__ import annotations

import os
import re

from models import SourceApp, SourceResult
from sources.base import CollectConfig, SourcePlugin


class GitHubSource(SourcePlugin):
    name = "github"

    def collect(self, client, cfg: CollectConfig, candidates: list[SourceApp] | None = None) -> SourceResult:
        if not candidates:
            return SourceResult(source=self.name, items=[], metadata={"retrieved": 0})
        items: list[SourceApp] = []
        token = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        count = 0
        for app in candidates:
            if count >= min(120, cfg.limit):
                break
            home = str(app.homepage or "")
            m = re.search(r"github\.com/([^/]+/[^/#?]+)", home)
            if not m:
                continue
            repo = m.group(1)
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            try:
                data = client.client.get(url, headers=headers, timeout=20.0)
                if data.status_code >= 400:
                    continue
                rel = data.json()
            except Exception:
                continue
            items.append(
                SourceApp(
                    source=self.name,
                    source_id=repo,
                    name=app.name,
                    category=app.category,
                    homepage=app.homepage,
                    upstream_repo=f"https://github.com/{repo}",
                    version=rel.get("tag_name") or rel.get("name"),
                    summary=rel.get("name") or "latest release",
                    raw_url=url,
                )
            )
            count += 1
        return SourceResult(source=self.name, items=items, metadata={"retrieved": len(items)})
