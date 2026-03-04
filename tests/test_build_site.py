from build_site import _display_version, _parse_evidence


def test_display_version_priority() -> None:
    row = {
        "latest_version_debian": "1",
        "latest_version_arch": "2",
        "latest_version_flathub": "3",
        "latest_version_upstream": "4",
    }
    assert _display_version(row) == "4"


def test_parse_evidence_pipe_fallback() -> None:
    assert _parse_evidence("one | two | three") == ["one", "two", "three"]
