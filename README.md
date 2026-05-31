# Shiori MCP
<p align="center">
  <a href="https://buymeacoffee.com/rusty4" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50">
  </a>
</p>



<!-- mcp-name: io.github.rusty4444/shiori-mcp -->

A Model Context Protocol (MCP) server for [Shiori](https://github.com/go-shiori/shiori), the self-hosted bookmark and read-it-later manager.

## Capabilities

- Verify Shiori connectivity and authentication
- List bookmarks
- Search bookmarks by title, URL, excerpt, and tag
- Get one bookmark by id or exact URL from the bookmark list
- Add bookmarks with Shiori's required tag-object format
- Update bookmarks via either a full-bookmark payload or common field parameters
- Delete bookmarks by id list
- List tags and bookmark counts
- Rename tags
- List accounts visible to the authenticated session

## Installation

```bash
pipx install git+https://github.com/rusty4444/shiori-mcp.git
```

Or from a checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

| Variable | Required | Description |
|---|---:|---|
| `SHIORI_BASE_URL` | Yes | Base URL of the Shiori instance, e.g. `https://shiori.example.com` |
| `SHIORI_SESSION_ID` | Optional | Existing Shiori session id; skips login if provided |
| `SHIORI_USERNAME` | Required unless session id is set | Shiori username |
| `SHIORI_PASSWORD` | Required unless session id is set | Shiori password |
| `SHIORI_TIMEOUT` | No | HTTP timeout in seconds, default `20` |

## MCP client config

```json
{
  "mcpServers": {
    "shiori": {
      "command": "shiori-mcp",
      "env": {
        "SHIORI_BASE_URL": "https://shiori.example.com",
        "SHIORI_USERNAME": "your-username",
        "SHIORI_PASSWORD": "your-password"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|---|---|
| `shiori_health_check` | Verify API connectivity/authentication |
| `shiori_list_bookmarks` | List bookmarks with client-side limit/offset |
| `shiori_search_bookmarks` | Search bookmarks by text and/or tag |
| `shiori_get_bookmark` | Get one bookmark by id from the bookmark list |
| `shiori_get_bookmark_by_url` | Get one bookmark by exact URL |
| `shiori_add_bookmark` | Add a bookmark with optional tags/archive/public flags |
| `shiori_update_bookmark` | Update a bookmark using full Shiori bookmark JSON |
| `shiori_update_bookmark_fields` | Update common fields without manually constructing full JSON |
| `shiori_delete_bookmark` | Delete one bookmark id |
| `shiori_delete_bookmarks` | Delete bookmark ids from a JSON array |
| `shiori_list_tags` | List tags and bookmark counts |
| `shiori_rename_tag` | Rename a tag |
| `shiori_list_accounts` | List accounts visible to this session |

## Development and validation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
ruff check .
pytest
python scripts/live_docs_test.py
```

`live_docs_test.py` validates Shiori public API documentation and repository pages without credentials. Authenticated read/write API behaviours are covered with mocked HTTP tests.

Optional LLM validation can be run with any configured OpenAI-compatible endpoint. For local Aeon validation, set `AEON_BASE_URL` and optionally `AEON_MODEL` / `AEON_API_KEY` before running `python scripts/model_validate.py`.

## API note

This server targets Shiori's documented legacy API under `/api/*` because the new API v1 is still documented as in development and self-documented at `/swagger/index.html` on running instances.

## Safety

The write-capable tools mutate a Shiori bookmark database. Keep credentials in environment variables or a secret manager, never in source control.

This project was developed with the assistance of AI tools.
