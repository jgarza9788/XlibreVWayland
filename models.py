from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SourceApp(BaseModel):
    source: str
    source_id: str
    name: str
    category: str | None = None
    homepage: HttpUrl | None = None
    upstream_repo: HttpUrl | None = None
    version: str | None = None
    summary: str | None = None
    raw_url: str | None = None
    popularity: float | None = None
    toolkit_guess: str | None = None


class AppRecord(BaseModel):
    app_id: str
    name: str
    category: str
    homepage: str | None = None
    upstream_repo: str | None = None
    latest_version_upstream: str | None = None
    latest_version_flathub: str | None = None
    latest_version_arch: str | None = None
    latest_version_debian: str | None = None
    wayland_score: int = Field(default=0, ge=0, le=5)
    xlibre_score: int = Field(default=0, ge=0, le=5)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_wayland: list[str]
    evidence_xlibre: list[str]
    toolkit_guess: Literal["GTK", "Qt", "Electron", "SDL", "CLI", "unknown"]
    run_mode_guess: Literal["native-wayland", "xwayland", "x11", "unknown"]
    sources_used: list[str]
    notes: str = ""


class SourceResult(BaseModel):
    source: str
    items: list[SourceApp]
    metadata: dict[str, str | int | float] = {}
