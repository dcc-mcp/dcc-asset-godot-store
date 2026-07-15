from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "godot-asset-store"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


store = load("_godot_store")


def test_search_parser() -> None:
    parser = store.SearchParser()
    parser.feed(
        """
        <div id="search-results"><div class="item">
          <h3 class="name"><a href="/asset/ramokz/phantom-camera/">Phantom Camera</a></h3>
          <p class="details">by <a href="/publisher/ramokz/">Ramokz</a> | MIT</p>
          <p class="snippet">A reusable camera addon.</p>
          <a href="/search/?tags%5B%5D=camera">Camera</a>
        </div></div>
        """
    )
    assert parser.items == [
        {
            "tags": ["Camera"],
            "publisher": "ramokz",
            "slug": "phantom-camera",
            "source_url": "https://store.godotengine.org/asset/ramokz/phantom-camera/",
            "name": "Phantom Camera",
            "publisher_name": "Ramokz",
            "description": "A reusable camera addon.",
            "license": "MIT",
        }
    ]


def test_version_parser_and_compatibility() -> None:
    parser = store.VersionParser()
    parser.feed(
        """
        <select id="version-dropdown">
          <option data-id="1088" data-version="v0.11" data-min-display-version="4.4"
            data-max-display-version="Undefined" data-size="850 KB"
            data-url="/asset/ramokz/phantom-camera/download/1088/"
            value="assets/3/phantom-camera-0.11.zip">Version</option>
          <option data-id="9" data-version="0.9.1.2" data-min-display-version="4.2"
            data-max-display-version="Undefined" data-size="886 KB"
            data-url="/asset/ramokz/phantom-camera/download/9/"
            value="assets/3/phantom-camera-0.9.1.2.zip">Version</option>
        </select>
        """
    )
    assert store.select_version(parser.versions, godot_version="4.3")["id"] == "9"
    assert store.select_version(parser.versions, version="v0.11")["id"] == "1088"


def test_skill_contract() -> None:
    from dcc_mcp_core import validate_skill

    report = validate_skill(str(SKILL))
    assert not report.has_errors, report
