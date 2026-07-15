from __future__ import annotations

import os

from test_godot_store import test_search_parser, test_skill_contract, test_version_parser_and_compatibility


def main() -> None:
    test_search_parser()
    test_version_parser_and_compatibility()
    test_skill_contract()
    if os.environ.get("RUN_LIVE_API_SMOKE") == "true":
        from test_godot_store import store

        asset = store.inspect_asset("ramokz", "phantom-camera")
        assert asset["versions"]
        assert asset["package_type"] == "addon"
    else:
        print("skip live Godot Asset Store API smoke")


if __name__ == "__main__":
    main()
