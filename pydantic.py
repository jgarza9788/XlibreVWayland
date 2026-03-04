from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

HttpUrl = str


def Field(default=None, ge=None, le=None, default_factory=None):
    if default_factory is not None:
        return field(default_factory=default_factory)
    return default


class BaseModel:
    def __init__(self, **kwargs):
        hints = getattr(self, "__annotations__", {})
        for k in hints:
            if k in kwargs:
                setattr(self, k, kwargs[k])
            elif hasattr(type(self), k):
                setattr(self, k, getattr(type(self), k))
            else:
                setattr(self, k, None)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        out = {}
        for k in getattr(self, "__annotations__", {}):
            v = getattr(self, k)
            if isinstance(v, list):
                out[k] = [x.model_dump(mode=mode) if hasattr(x, "model_dump") else x for x in v]
            elif hasattr(v, "model_dump"):
                out[k] = v.model_dump(mode=mode)
            else:
                out[k] = v
        return out
