from __future__ import annotations

from typing import Any

from _godot_store import inspect_asset
from dcc_mcp_core.skill import skill_entry, skill_exception, skill_success


@skill_entry
def main(publisher: str, slug: str, **_: Any) -> dict[str, Any]:
    try:
        asset = inspect_asset(publisher, slug)
        return skill_success("Godot Asset Store asset inspected", asset=asset)
    except Exception as exc:  # noqa: BLE001 - Skill boundary returns a structured error for any failure.
        return skill_exception(exc, message="Failed to inspect the Godot Asset Store asset")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
