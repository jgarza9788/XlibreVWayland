from models import SourceApp
from scoring import score_from_sources


def test_wayland_native_keyword_boosts_score() -> None:
    app = SourceApp(source="flathub", source_id="org.demo.App", name="Demo", summary="native Wayland client", category="Utility")
    score = score_from_sources([app])
    assert score.wayland >= 4
    assert score.run_mode == "native-wayland"


def test_x11_only_lowers_wayland() -> None:
    app = SourceApp(source="arch", source_id="xapp", name="xapp", summary="legacy X11 only program", category="x11")
    score = score_from_sources([app])
    assert score.wayland <= 1
    assert score.xlibre >= 4
