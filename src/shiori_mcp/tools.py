"""MCP tools for Shiori."""

from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import client as api

BookmarkId = Annotated[int, Field(description="Shiori bookmark id")]


def register_tools(mcp: FastMCP) -> None:
    """Register Shiori MCP tools."""

    @mcp.tool()
    async def shiori_health_check() -> str:
        """Verify Shiori API connectivity and authentication with a small read-only request."""
        try:
            return _json(api.health_check())
        except Exception as exc:
            return f"Error checking Shiori health: {exc}"

    @mcp.tool()
    async def shiori_list_bookmarks(
        limit: Annotated[int, Field(description="Maximum number of bookmarks to return from the local result set")]= 30,
        offset: Annotated[int, Field(description="Number of matching bookmarks to skip")]= 0,
    ) -> str:
        """List Shiori bookmarks from the default Shiori bookmarks endpoint."""
        try:
            data = api.search_bookmarks(limit=max(1, min(limit, 100)), offset=max(0, offset))
            return _format_bookmarks(data)
        except Exception as exc:
            return f"Error listing Shiori bookmarks: {exc}"

    @mcp.tool()
    async def shiori_search_bookmarks(
        query: Annotated[str | None, Field(description="Case-insensitive text to match against bookmark title, URL, or excerpt")]= None,
        tag: Annotated[str | None, Field(description="Optional tag name to filter bookmarks by exact tag name")]= None,
        limit: Annotated[int, Field(description="Maximum number of matching bookmarks to return")]= 30,
        offset: Annotated[int, Field(description="Number of matching bookmarks to skip")]= 0,
    ) -> str:
        """Search Shiori bookmarks client-side by text and/or tag."""
        try:
            data = api.search_bookmarks(query=query, tag=tag, limit=max(1, min(limit, 100)), offset=max(0, offset))
            return _format_bookmarks(data)
        except Exception as exc:
            return f"Error searching Shiori bookmarks: {exc}"

    @mcp.tool()
    async def shiori_get_bookmark(bookmark_id: BookmarkId) -> str:
        """Get one Shiori bookmark by id from the bookmark list."""
        try:
            return _json(api.get_bookmark(bookmark_id))
        except Exception as exc:
            return f"Error getting Shiori bookmark {bookmark_id}: {exc}"

    @mcp.tool()
    async def shiori_get_bookmark_by_url(
        url: Annotated[str, Field(description="Exact Shiori bookmark URL to look up")],
    ) -> str:
        """Get one Shiori bookmark by exact URL from the bookmark list."""
        try:
            return _json(api.get_bookmark_by_url(url))
        except Exception as exc:
            return f"Error getting Shiori bookmark by URL: {exc}"

    @mcp.tool()
    async def shiori_add_bookmark(
        url: Annotated[str, Field(description="URL to save in Shiori")],
        title: Annotated[str | None, Field(description="Optional title hint; Shiori may fetch and override it automatically")]= None,
        excerpt: Annotated[str | None, Field(description="Optional excerpt hint; Shiori may fetch and override it automatically")]= None,
        tags: Annotated[str | None, Field(description="Optional comma-separated tag names; converted to Shiori's required [{name: ...}] format")]= None,
        public: Annotated[bool, Field(description="Whether the bookmark should be public/shared")]= False,
        create_archive: Annotated[bool, Field(description="Whether Shiori should create an archived copy of the page")]= True,
    ) -> str:
        """Add a bookmark to Shiori."""
        try:
            return _json(api.add_bookmark(url, title=title, excerpt=excerpt, tags=tags, public=public, create_archive=create_archive))
        except Exception as exc:
            return f"Error adding Shiori bookmark: {exc}"

    @mcp.tool()
    async def shiori_update_bookmark(
        bookmark_json: Annotated[str, Field(description="Full Shiori bookmark JSON object including id and any fields to update; tags must be objects like {\"name\":\"tag\"}")],
    ) -> str:
        """Update a Shiori bookmark using the full bookmark JSON object expected by the legacy API."""
        try:
            bookmark = json.loads(bookmark_json)
            if not isinstance(bookmark, dict) or "id" not in bookmark:
                raise ValueError("bookmark_json must decode to an object with an id field")
            return _json(api.update_bookmark(bookmark))
        except Exception as exc:
            return f"Error updating Shiori bookmark: {exc}"

    @mcp.tool()
    async def shiori_update_bookmark_fields(
        bookmark_id: BookmarkId,
        title: Annotated[str | None, Field(description="Optional replacement title")]= None,
        excerpt: Annotated[str | None, Field(description="Optional replacement excerpt")]= None,
        public: Annotated[bool | None, Field(description="Optional public/shared flag")]= None,
        tags: Annotated[str | None, Field(description="Optional comma-separated replacement tag names")]= None,
        create_archive: Annotated[bool | None, Field(description="Optional createArchive flag")]= None,
    ) -> str:
        """Patch common bookmark fields by fetching the current bookmark, modifying it, then sending Shiori's full update payload."""
        try:
            bookmark = api.get_bookmark(bookmark_id)
            if title is not None:
                bookmark["title"] = title
            if excerpt is not None:
                bookmark["excerpt"] = excerpt
            if public is not None:
                bookmark["public"] = 1 if public else 0
            if tags is not None:
                bookmark["tags"] = [{"name": t.strip()} for t in tags.split(",") if t.strip()]
            if create_archive is not None:
                bookmark["createArchive"] = create_archive
            return _json(api.update_bookmark(bookmark))
        except Exception as exc:
            return f"Error updating Shiori bookmark fields for {bookmark_id}: {exc}"

    @mcp.tool()
    async def shiori_delete_bookmark(
        bookmark_id: BookmarkId,
    ) -> str:
        """Delete one Shiori bookmark by id."""
        try:
            return _json(api.delete_bookmarks([bookmark_id]))
        except Exception as exc:
            return f"Error deleting Shiori bookmark {bookmark_id}: {exc}"

    @mcp.tool()
    async def shiori_delete_bookmarks(
        ids_json: Annotated[str, Field(description="JSON array of Shiori bookmark ids to delete, for example [1,2,3]")],
    ) -> str:
        """Delete one or more Shiori bookmarks by id."""
        try:
            ids = json.loads(ids_json)
            if not isinstance(ids, list) or not all(isinstance(x, int) for x in ids):
                raise ValueError("ids_json must decode to a JSON array of integers")
            return _json(api.delete_bookmarks(ids))
        except Exception as exc:
            return f"Error deleting Shiori bookmarks: {exc}"

    @mcp.tool()
    async def shiori_list_tags() -> str:
        """List Shiori tags and bookmark counts."""
        try:
            return _format_tags(api.list_tags())
        except Exception as exc:
            return f"Error listing Shiori tags: {exc}"

    @mcp.tool()
    async def shiori_rename_tag(
        tag_id: Annotated[int, Field(description="Shiori tag id to rename")],
        name: Annotated[str, Field(description="New tag name")],
    ) -> str:
        """Rename a Shiori tag."""
        try:
            return _json(api.rename_tag(tag_id, name))
        except Exception as exc:
            return f"Error renaming Shiori tag {tag_id}: {exc}"

    @mcp.tool()
    async def shiori_list_accounts() -> str:
        """List Shiori user accounts visible to the authenticated session."""
        try:
            return _json(api.list_accounts())
        except Exception as exc:
            return f"Error listing Shiori accounts: {exc}"


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _format_bookmarks(data: dict[str, Any]) -> str:
    bookmarks = data.get("bookmarks", [])
    if not bookmarks:
        return f"No Shiori bookmarks found. Metadata: {_json({k: v for k, v in data.items() if k != 'bookmarks'})}"
    lines = [f"Shiori bookmarks ({len(bookmarks)} shown, total={data.get('total', len(bookmarks))}, offset={data.get('offset', 0)}):"]
    for b in bookmarks:
        tags = ",".join(str(t.get("name")) for t in b.get("tags", []) if isinstance(t, dict) and t.get("name"))
        lines.append(
            f"- #{b.get('id')} {b.get('title') or '(untitled)'} | public={b.get('public')} hasArchive={b.get('hasArchive')} "
            f"hasContent={b.get('hasContent')} | tags={tags} | url={b.get('url')}"
        )
    return "\n".join(lines)


def _format_tags(tags: list[dict[str, Any]]) -> str:
    if not tags:
        return "No Shiori tags found."
    lines = [f"Shiori tags ({len(tags)}):"]
    for tag in tags:
        lines.append(f"- #{tag.get('id')} {tag.get('name')} bookmarks={tag.get('nBookmarks')}")
    return "\n".join(lines)
