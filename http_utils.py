from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx
from diskcache import Cache


class CachedHttpClient:
    def __init__(self, cache_dir: str = ".cache/http", min_interval: float = 0.1):
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
        self.cache = Cache(cache_dir)
        self.min_interval = min_interval
        self._last_call_ts = 0.0

    def _wait(self) -> None:
        elapsed = time.time() - self._last_call_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    @staticmethod
    def _key(url: str, params: dict[str, Any] | None = None) -> str:
        raw = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_json(self, url: str, params: dict[str, Any] | None = None, retries: int = 4) -> Any:
        key = self._key(url, params)
        if key in self.cache:
            return self.cache[key]
        backoff = 0.5
        for i in range(retries):
            try:
                self._wait()
                resp = self.client.get(url, params=params)
                self._last_call_ts = time.time()
                resp.raise_for_status()
                data = resp.json()
                self.cache[key] = data
                return data
            except Exception:
                if i == retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError("unreachable")

    def get_text(self, url: str, params: dict[str, Any] | None = None, retries: int = 4) -> str:
        key = self._key(url, params)
        if key in self.cache:
            return self.cache[key]
        backoff = 0.5
        for i in range(retries):
            try:
                self._wait()
                resp = self.client.get(url, params=params)
                self._last_call_ts = time.time()
                resp.raise_for_status()
                text = resp.text
                self.cache[key] = text
                return text
            except Exception:
                if i == retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError("unreachable")
