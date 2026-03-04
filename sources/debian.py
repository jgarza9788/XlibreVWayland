from __future__ import annotations

import gzip
import io
import random
import subprocess

import httpx

from models import SourceApp, SourceResult
from sources.base import CollectConfig, SourcePlugin


class DebianSource(SourcePlugin):
    name = "debian"
    PACKAGE_URL = "https://deb.debian.org/debian/dists/bookworm/main/binary-amd64/Packages.gz"

    def collect(self, client, cfg: CollectConfig) -> SourceResult:
        try:
            text = self._fetch_packages_text(client)
            return self._parse_package_index(text, cfg)
        except Exception:
            return self._fallback_local_dpkg(cfg)

    def _parse_package_index(self, text: str, cfg: CollectConfig) -> SourceResult:
        rng = random.Random(cfg.seed)
        blocks = text.split("\n\n")
        rng.shuffle(blocks)
        items: list[SourceApp] = []
        for block in blocks:
            if "Package:" not in block:
                continue
            fields: dict[str, str] = {}
            for line in block.splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    fields[k] = v
            pkg = fields.get("Package")
            if not pkg:
                continue
            section = fields.get("Section", "unknown")
            if not any(tag in section for tag in ["x11", "gnome", "kde", "editors", "games", "video", "sound", "utils", "web"]):
                continue
            items.append(
                SourceApp(
                    source=self.name,
                    source_id=pkg,
                    name=pkg,
                    category=section,
                    version=fields.get("Version"),
                    summary=fields.get("Description"),
                    raw_url=f"https://packages.debian.org/bookworm/{pkg}",
                )
            )
            if len(items) >= max(cfg.limit * 2, 900):
                break
        return SourceResult(source=self.name, items=items, metadata={"retrieved": len(items), "index": self.PACKAGE_URL})

    def _fallback_local_dpkg(self, cfg: CollectConfig) -> SourceResult:
        cmd = ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Section}\t${binary:Summary}\n"]
        out = subprocess.check_output(cmd, text=True)
        rows = out.strip().splitlines()
        rng = random.Random(cfg.seed)
        rng.shuffle(rows)
        items: list[SourceApp] = []
        for row in rows:
            parts = row.split("\t")
            if len(parts) < 4:
                continue
            pkg, version, section, summary = parts[0], parts[1], parts[2], parts[3]
            items.append(
                SourceApp(
                    source=self.name,
                    source_id=pkg,
                    name=pkg,
                    category=section or "unknown",
                    version=version,
                    summary=summary,
                    raw_url=f"https://packages.ubuntu.com/search?keywords={pkg}",
                )
            )
            if len(items) >= max(cfg.limit * 2, 900):
                break
        return SourceResult(source=self.name, items=items, metadata={"retrieved": len(items), "fallback": "local-dpkg"})

    def _fetch_packages_text(self, client) -> str:
        cache_key = f"debian-packages::{self.PACKAGE_URL}"
        if cache_key in client.cache:
            return client.cache[cache_key]
        resp = httpx.get(self.PACKAGE_URL, timeout=60.0, follow_redirects=True)
        resp.raise_for_status()
        text = gzip.GzipFile(fileobj=io.BytesIO(resp.content)).read().decode("utf-8", errors="ignore")
        client.cache[cache_key] = text
        return text
