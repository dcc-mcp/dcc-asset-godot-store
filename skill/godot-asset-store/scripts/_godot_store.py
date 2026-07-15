from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_URL = "https://store.godotengine.org"
TERMS_URL = f"{BASE_URL}/terms/"
HEADERS = {"User-Agent": "dcc-mcp-godot-store/0.1"}
PACKAGE_TYPES = {0: "addon", 1: "project"}
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _request(url: str, timeout: int = 30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=timeout)


def get_text(path: str) -> str:
    with _request(urllib.parse.urljoin(BASE_URL, path)) as response:
        return response.read().decode("utf-8")


def get_json(path: str) -> Dict[str, Any]:
    return json.loads(get_text(path))


def _classes(attrs: List[Tuple[str, Optional[str]]]) -> set[str]:
    values = dict(attrs).get("class") or ""
    return set(values.split())


class SearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: List[Dict[str, Any]] = []
        self.current: Optional[Dict[str, Any]] = None
        self.depth = 0
        self.capture: Optional[str] = None
        self.section: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        classes = _classes(attrs)
        if tag == "div" and "item" in classes and self.current is None:
            self.current = {"tags": []}
            self.depth = 1
            return
        if self.current is None:
            return
        if tag == "div":
            self.depth += 1
        if tag == "p" and "details" in classes:
            self.section = self.capture = "details"
        elif tag == "p" and "snippet" in classes:
            self.section = self.capture = "description"
        elif tag == "a":
            href = attrs_dict.get("href") or ""
            parts = [part for part in href.split("?")[0].split("/") if part]
            if len(parts) == 3 and parts[0] == "asset":
                self.current.update(
                    {
                        "publisher": parts[1],
                        "slug": parts[2],
                        "source_url": urllib.parse.urljoin(BASE_URL, href),
                    }
                )
                self.capture = "name"
            elif href.startswith("/publisher/"):
                self.capture = "publisher_name"
            elif (
                "tags%5B%5D=" in href
                or "tags[]=" in href
                or "query=%23" in href
                or "query=#" in href
            ):
                self.capture = "tag"

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        if tag == "a":
            self.capture = self.section
        elif tag == "p":
            self.section = self.capture = None
        if tag == "div":
            self.depth -= 1
            if self.depth == 0:
                if self.current.get("slug"):
                    self.current["license"] = _license_from_details(
                        self.current.pop("details", "")
                    )
                    self.items.append(self.current)
                self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is None or not self.capture:
            return
        value = " ".join(data.split())
        if not value:
            return
        if self.capture == "tag":
            self.current["tags"].append(value)
        else:
            previous = self.current.get(self.capture, "")
            self.current[self.capture] = f"{previous} {value}".strip()


class VersionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_versions = False
        self.versions: List[Dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "select" and attrs_dict.get("id") == "version-dropdown":
            self.in_versions = True
            return
        if tag != "option" or not self.in_versions:
            return
        self.versions.append(
            {
                "id": attrs_dict.get("data-id"),
                "version": attrs_dict.get("data-version"),
                "godot_version_min": _undefined(attrs_dict.get("data-min-display-version")),
                "godot_version_max": _undefined(attrs_dict.get("data-max-display-version")),
                "size": attrs_dict.get("data-size"),
                "download_path": attrs_dict.get("data-url"),
                "archive_name": Path(attrs_dict.get("value") or "asset.zip").name,
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if tag == "select" and self.in_versions:
            self.in_versions = False


def _undefined(value: Optional[str]) -> Optional[str]:
    if not value or value.lower() in {"undefined", "none"}:
        return None
    return value


def _license_from_details(details: str) -> Optional[str]:
    if "|" not in details:
        return None
    value = details.rsplit("|", 1)[-1].strip()
    return value or None


def _safe_slug(value: str, field: str) -> str:
    value = value.strip().lower()
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid {field}: {value!r}")
    return value


def search_assets(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    parser = SearchParser()
    parser.feed(get_text(f"/search/?{urllib.parse.urlencode({'query': query})}"))
    return parser.items[: max(1, min(limit, 25))]


def inspect_asset(publisher: str, slug: str) -> Dict[str, Any]:
    publisher = _safe_slug(publisher, "publisher")
    slug = _safe_slug(slug, "slug")
    detail = get_json(f"/api/v1/assets/{publisher}/{slug}/")
    parser = VersionParser()
    parser.feed(get_text(f"/asset/{publisher}/{slug}/"))
    detail["package_type"] = PACKAGE_TYPES.get(detail.get("type"), "auto")
    detail["versions"] = parser.versions
    detail["terms_url"] = TERMS_URL
    return detail


def _version_tuple(value: str) -> Tuple[int, ...]:
    numbers = re.findall(r"\d+", value or "")
    return tuple(int(number) for number in numbers)


def select_version(
    versions: List[Dict[str, Any]],
    version: Optional[str] = None,
    godot_version: Optional[str] = None,
) -> Dict[str, Any]:
    if version:
        wanted = version.lower().lstrip("v")
        matches = [item for item in versions if str(item.get("version", "")).lower().lstrip("v") == wanted]
    else:
        matches = list(versions)
    if godot_version:
        current = _version_tuple(godot_version)
        matches = [
            item
            for item in matches
            if (not item.get("godot_version_min") or current >= _version_tuple(item["godot_version_min"]))
            and (not item.get("godot_version_max") or current <= _version_tuple(item["godot_version_max"]))
        ]
    if not matches:
        constraint = f"version={version or 'latest'}, godot_version={godot_version or 'any'}"
        raise ValueError(f"No compatible asset package found ({constraint})")
    return matches[0]


def download_package(
    detail: Dict[str, Any],
    selected: Dict[str, Any],
    output_dir: str,
) -> Dict[str, Any]:
    if int(detail.get("price_cent") or 0) > 0:
        raise ValueError("Paid assets require interactive checkout and cannot be downloaded by this skill")
    download_path = selected.get("download_path")
    if not download_path:
        raise ValueError("Selected asset version has no download URL")
    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / str(selected.get("archive_name") or "asset.zip")
    temporary = target.with_suffix(target.suffix + ".part")
    digest = hashlib.sha256()
    try:
        with _request(urllib.parse.urljoin(BASE_URL, download_path), timeout=180) as response:
            with temporary.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    stream.write(chunk)
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    publisher = detail["publisher"]["slug"]
    slug = detail["slug"]
    version_id = selected["id"]
    return {
        "asset_id": f"godot-store:{publisher}/{slug}@{version_id}",
        "archive_path": str(target),
        "sha256": digest.hexdigest(),
        "package_type": detail.get("package_type", "auto"),
        "version": selected.get("version"),
        "godot_version_min": selected.get("godot_version_min"),
        "godot_version_max": selected.get("godot_version_max"),
        "license": detail.get("license_type"),
        "publisher": detail["publisher"].get("name"),
        "source_url": detail.get("store_url"),
        "upstream_source": detail.get("source"),
        "terms_url": TERMS_URL,
    }
