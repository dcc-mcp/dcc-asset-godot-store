from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_core.skill import skill_entry, skill_error, skill_exception, skill_success

from _godot_store import TERMS_URL, download_package, inspect_asset, select_version


@skill_entry
def main(
    publisher: str,
    slug: str,
    output_dir: str,
    accept_terms: bool,
    version: Optional[str] = None,
    godot_version: Optional[str] = None,
    **_: Any,
) -> Dict[str, Any]:
    if not accept_terms:
        return skill_error(
            "Godot Asset Store terms must be accepted before downloading",
            f"Review {TERMS_URL} and retry with accept_terms=true",
            terms_url=TERMS_URL,
        )
    try:
        detail = inspect_asset(publisher, slug)
        selected = select_version(detail["versions"], version, godot_version)
        package = download_package(detail, selected, output_dir)
        return skill_success("Godot Asset Store package downloaded", package=package)
    except Exception as exc:
        return skill_exception(exc, message="Failed to download the Godot Asset Store package")


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main

    run_main(main)
