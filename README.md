# DCC-MCP Godot Asset Store

Discover and download reusable packages from the
[Godot Asset Store](https://store.godotengine.org/) without coupling remote
catalog logic to the Godot adapter.

The provider returns a `godot_asset_package` containing the archive path,
SHA-256 digest, package type, version compatibility, license, and source URLs.
The bundled `godot-assets` host skill plans and installs that package into a
Godot project.

## Install

```bash
dcc-mcp-cli marketplace add dcc-mcp/dcc-asset-godot-store
dcc-mcp-cli marketplace install dcc-asset-godot-store
```

## Tools

- `search_godot_assets`
- `inspect_godot_asset`
- `download_godot_asset`

`download_godot_asset` supports free packages and requires explicit acceptance
of the [Godot Asset Store terms](https://store.godotengine.org/terms/).
