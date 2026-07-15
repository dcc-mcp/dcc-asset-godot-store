from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success

from _godot_store import search_assets


@skill_entry
def main(query: str, limit: int = 10, **_: Any) -> Dict[str, Any]:
    try:
        assets = search_assets(query, limit)
        return skill_success("Godot Asset Store assets found", assets=assets, count=len(assets))
    except Exception as exc:
        return skill_exception(exc, message="Failed to search the Godot Asset Store")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
