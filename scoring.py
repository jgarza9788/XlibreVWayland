from __future__ import annotations

import re
from dataclasses import dataclass

from models import SourceApp


@dataclass
class ScoreResult:
    wayland: int
    xlibre: int
    toolkit: str
    run_mode: str
    confidence: float
    evidence_wayland: list[str]
    evidence_xlibre: list[str]
    notes: str


TOOLKIT_RULES = [
    ("gtk", "GTK"),
    ("qt", "Qt"),
    ("electron", "Electron"),
    ("sdl", "SDL"),
    ("terminal", "CLI"),
    ("cli", "CLI"),
]


def detect_toolkit(text: str) -> str:
    ltxt = text.lower()
    for needle, value in TOOLKIT_RULES:
        if needle in ltxt:
            return value
    return "unknown"


def score_from_sources(apps: list[SourceApp]) -> ScoreResult:
    blob = " ".join(filter(None, [a.name + " " + (a.summary or "") + " " + (a.category or "") for a in apps]))
    toolkit = next((a.toolkit_guess for a in apps if a.toolkit_guess), None) or detect_toolkit(blob)

    e_w: list[str] = []
    e_x: list[str] = []
    wayland = 3
    xlibre = 4
    mode = "unknown"

    ltxt = blob.lower()
    if re.search(r"\bwayland\b", ltxt):
        wayland = 4
        e_w.append("Metadata mentions Wayland support")
    if "native wayland" in ltxt or "wlroots" in ltxt:
        wayland = 5
        mode = "native-wayland"
        e_w.append("Indicates native Wayland stack")
    if "xwayland" in ltxt:
        wayland = min(wayland, 3)
        mode = "xwayland"
        e_w.append("Runs via XWayland")
    if "x11 only" in ltxt:
        wayland = 1
        mode = "x11"
        e_w.append("Marked X11-only")

    if toolkit in {"GTK", "Qt", "SDL", "Electron"}:
        e_w.append(f"Toolkit {toolkit} commonly supports Wayland")
        wayland = max(wayland, 4 if toolkit != "Electron" else 3)
        e_x.append(f"Toolkit {toolkit} supports X11/XLibre-style sessions")
        xlibre = max(xlibre, 4)
    if toolkit == "CLI":
        wayland = max(wayland, 4)
        xlibre = 5
        mode = "x11" if mode == "unknown" else mode
        e_w.append("Terminal app usually compositor-agnostic")
        e_x.append("Terminal app runs in X11 terminals")

    if re.search(r"\b(x11|xorg|xcb|xlib)\b", ltxt):
        xlibre = 5
        e_x.append("Metadata references X11/Xorg APIs")
    if "wayland-only" in ltxt:
        xlibre = min(xlibre, 1)
        e_x.append("Wayland-only note reduces XLibre confidence")

    if mode == "unknown":
        mode = "native-wayland" if wayland >= 4 else "x11"

    uniq_w = list(dict.fromkeys(e_w))
    uniq_x = list(dict.fromkeys(e_x))
    evidence_count = len(uniq_w) + len(uniq_x)
    confidence = min(1.0, 0.35 + evidence_count * 0.08 + (0.1 if len(apps) > 1 else 0))

    return ScoreResult(
        wayland=max(0, min(5, wayland)),
        xlibre=max(0, min(5, xlibre)),
        toolkit=toolkit if toolkit in {"GTK", "Qt", "Electron", "SDL", "CLI"} else "unknown",
        run_mode=mode if mode in {"native-wayland", "xwayland", "x11"} else "unknown",
        confidence=round(confidence, 3),
        evidence_wayland=uniq_w,
        evidence_xlibre=uniq_x,
        notes="Heuristic scoring based on toolkit + metadata mentions; XLibre treated as X11/Xorg-style compatibility.",
    )
