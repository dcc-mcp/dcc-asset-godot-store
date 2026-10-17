from __future__ import annotations

from typing import Any

from _godot_store import search_assets
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


@skill_entry
def main(query: str, limit: int = 10, **_: Any) -> dict[str, Any]:
    try:
        assets = search_assets(query, limit)
        return skill_success("Godot Asset Store assets found", assets=assets, count=len(assets))
    except Exception as exc:  # noqa: BLE001 - Skill boundary returns a structured error for any failure.
        return skill_exception(exc, message="Failed to search the Godot Asset Store")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
