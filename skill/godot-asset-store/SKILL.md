---
name: godot-asset-store
description: Search, inspect, and download reusable packages from the Godot Asset Store.
license: MIT
compatibility: "dcc-mcp-core 0.19+, Python 3.9+"
metadata:
  dcc-mcp:
    version: v0.1.0
    dcc: godot
    layer: domain
    lifecycle: experimental
    tags:
      - asset
      - godot
      - asset-store
      - addon
      - project
      - download
    search-hint: "godot asset store, godot addon, plugin, reusable game asset, download"
    produces: [godot_asset_package]
    tools: tools.yaml
---

# Godot Asset Store

Use this skill to discover and download packages from the Godot Asset Store.
It does not modify a Godot project. Pass the returned `package` to the bundled
`godot-assets` skill to plan and install it safely.

Downloads require `accept_terms: true`. Paid assets are reported but are not
downloaded because checkout and license acceptance require an interactive user.
