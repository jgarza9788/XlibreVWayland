from __future__ import annotations

from dataclasses import dataclass

from http_utils import CachedHttpClient
from models import SourceResult


@dataclass
class CollectConfig:
    limit: int
    seed: int


class SourcePlugin:
    name: str

    def collect(self, client: CachedHttpClient, cfg: CollectConfig) -> SourceResult:
        raise NotImplementedError
