---
name: shiori
description: Use the Shiori MCP server for bookmark/read-it-later capture, search, tags, and account discovery.
version: 0.1.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [shiori, mcp, bookmarks, read-it-later]
---

# Shiori MCP Skill

Use this skill when the user asks Hermes to connect to or automate Shiori.

## Setup

Configure the MCP server with:

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

Alternatively provide `SHIORI_SESSION_ID` to skip login.

## Tool selection

- Health/auth: `shiori_health_check`
- Reading/search: `shiori_list_bookmarks`, `shiori_search_bookmarks`, `shiori_get_bookmark`, `shiori_get_bookmark_by_url`
- Capture/edit/delete: `shiori_add_bookmark`, `shiori_update_bookmark`, `shiori_update_bookmark_fields`, `shiori_delete_bookmark`, `shiori_delete_bookmarks`
- Tags: `shiori_list_tags`, `shiori_rename_tag`
- Accounts: `shiori_list_accounts`

## Pitfalls

- Shiori legacy API tags are objects like `{ "name": "Interesting" }`, not bare strings. The add tool converts comma-separated tags for you.
- The update API expects a full bookmark object including `id`; fetch the bookmark first, then edit the JSON.
- The new API v1 is still in development; this server targets the documented legacy `/api/*` endpoints for stability.
