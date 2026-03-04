from scripts.build_report import _display_version, _parse_listish


def test_display_version_priority() -> None:
    row = {
        "latest_version_debian": "1",
        "latest_version_arch": "2",
        "latest_version_flathub": "3",
        "latest_version_upstream": "4",
    }
    assert _display_version(row) == "4"


def test_parse_listish_json_and_plain() -> None:
    assert _parse_listish('["a", "b"]') == ["a", "b"]
    assert _parse_listish('one | two') == ["one", "two"]
