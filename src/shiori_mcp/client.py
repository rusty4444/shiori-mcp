"""Thin Shiori legacy REST API client."""

from __future__ import annotations

import os
from typing import Any

import httpx

_BASE_URL: str | None = None
_USERNAME: str | None = None
_PASSWORD: str | None = None
_SESSION_ID: str | None = None
_TIMEOUT = 20.0


class ShioriError(RuntimeError):
    """Raised when the Shiori API returns an error."""


def configure(
    base_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    session_id: str | None = None,
    timeout: float | None = None,
) -> None:
    """Configure the Shiori API client."""
    global _BASE_URL, _USERNAME, _PASSWORD, _SESSION_ID, _TIMEOUT
    if base_url is not None:
        _BASE_URL = base_url.rstrip("/")
    if username is not None:
        _USERNAME = username
    if password is not None:
        _PASSWORD = password
    if session_id is not None:
        _SESSION_ID = session_id
    if timeout is not None:
        _TIMEOUT = timeout


def _base_url() -> str:
    base = (_BASE_URL or os.environ.get("SHIORI_BASE_URL") or "").rstrip("/")
    if not base:
        raise ShioriError("SHIORI_BASE_URL is required")
    return base


def _credentials() -> tuple[str | None, str | None]:
    return _USERNAME or os.environ.get("SHIORI_USERNAME"), _PASSWORD or os.environ.get("SHIORI_PASSWORD")


def session_id() -> str:
    """Return configured session id or log in with username/password."""
    global _SESSION_ID
    sid = _SESSION_ID or os.environ.get("SHIORI_SESSION_ID")
    if sid:
        return sid
    username, password = _credentials()
    if not username or not password:
        raise ShioriError("Authentication requires SHIORI_SESSION_ID or SHIORI_USERNAME and SHIORI_PASSWORD")
    data = {"username": username, "password": password, "remember": True, "owner": True}
    try:
        response = httpx.post(f"{_base_url()}/api/login", json=data, timeout=_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ShioriError(f"Login failed: HTTP {exc.response.status_code}: {exc.response.text[:500]}") from exc
    except httpx.HTTPError as exc:
        raise ShioriError(f"Login failed: {exc}") from exc
    payload = response.json()
    _SESSION_ID = str(payload.get("session") or "")
    if not _SESSION_ID:
        raise ShioriError("Login response did not include a session id")
    return _SESSION_ID


def _request(method: str, path: str, *, json_body: Any | None = None, params: dict[str, Any] | None = None) -> Any:
    headers = {"Accept": "application/json", "X-Session-Id": session_id()}
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    try:
        response = httpx.request(
            method,
            f"{_base_url()}{path}",
            headers=headers,
            params=_drop_none(params or {}),
            json=json_body,
            timeout=_TIMEOUT,
        )
        if response.status_code == 401 and _USERNAME and _PASSWORD:
            # Session expired: force a fresh login once and retry the request.
            global _SESSION_ID
            _SESSION_ID = None
            headers["X-Session-Id"] = session_id()
            response = httpx.request(
                method,
                f"{_base_url()}{path}",
                headers=headers,
                params=_drop_none(params or {}),
                json=json_body,
                timeout=_TIMEOUT,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ShioriError(f"{method} {path} failed: HTTP {exc.response.status_code}: {exc.response.text[:500]}") from exc
    except httpx.HTTPError as exc:
        raise ShioriError(f"{method} {path} failed: {exc}") from exc
    if response.status_code == 204 or not response.content:
        return {"ok": True}
    if "json" in response.headers.get("content-type", ""):
        return response.json()
    return {"ok": True, "text": response.text.strip()}


def _drop_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def _tag_objects(tags: str | list[str] | list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if tags is None:
        return []
    if isinstance(tags, str):
        names = [t.strip() for t in tags.split(",") if t.strip()]
        return [{"name": name} for name in names]
    out = []
    for tag in tags:
        if isinstance(tag, str):
            out.append({"name": tag})
        elif isinstance(tag, dict) and tag.get("name"):
            out.append({"name": str(tag["name"])})
    return out


def health_check() -> dict[str, Any]:
    data = list_bookmarks()
    return {"ok": True, "bookmarks_seen": len(data.get("bookmarks", [])), "page": data.get("page"), "maxPage": data.get("maxPage")}


def list_bookmarks() -> dict[str, Any]:
    data = _request("GET", "/api/bookmarks")
    if not isinstance(data, dict):
        raise ShioriError(f"Expected bookmark list object, got {type(data).__name__}")
    data.setdefault("bookmarks", [])
    return data


def search_bookmarks(query: str | None = None, tag: str | None = None, limit: int = 30, offset: int = 0) -> dict[str, Any]:
    data = list_bookmarks()
    bookmarks = data.get("bookmarks", [])
    if query:
        q = query.lower()
        bookmarks = [b for b in bookmarks if q in str(b.get("title", "")).lower() or q in str(b.get("url", "")).lower() or q in str(b.get("excerpt", "")).lower()]
    if tag:
        t = tag.lower()
        bookmarks = [b for b in bookmarks if any(t == str(x.get("name", "")).lower() for x in b.get("tags", []) if isinstance(x, dict))]
    total = len(bookmarks)
    return {"bookmarks": bookmarks[offset : offset + limit], "total": total, "limit": limit, "offset": offset}


def get_bookmark(bookmark_id: int) -> dict[str, Any]:
    for bookmark in list_bookmarks().get("bookmarks", []):
        if int(bookmark.get("id", -1)) == int(bookmark_id):
            return bookmark
    raise ShioriError(f"Bookmark id {bookmark_id} was not found in the bookmark list")


def get_bookmark_by_url(url: str) -> dict[str, Any]:
    for bookmark in list_bookmarks().get("bookmarks", []):
        if str(bookmark.get("url", "")) == url:
            return bookmark
    raise ShioriError(f"Bookmark URL {url} was not found in the bookmark list")


def add_bookmark(url: str, *, title: str | None = None, excerpt: str | None = None, public: bool = False, create_archive: bool = True, tags: str | None = None) -> dict[str, Any]:
    body = _drop_none({"url": url, "title": title, "excerpt": excerpt, "public": 1 if public else 0, "createArchive": create_archive, "tags": _tag_objects(tags)})
    data = _request("POST", "/api/bookmarks", json_body=body)
    if not isinstance(data, dict):
        raise ShioriError(f"Expected bookmark object after create, got {type(data).__name__}")
    return data


def update_bookmark(bookmark: dict[str, Any]) -> dict[str, Any]:
    data = _request("PUT", "/api/bookmarks", json_body=bookmark)
    if isinstance(data, dict) and data.get("ok") and bookmark.get("id"):
        return get_bookmark(int(bookmark["id"]))
    if not isinstance(data, dict):
        return get_bookmark(int(bookmark["id"]))
    return data


def delete_bookmarks(ids: list[int]) -> dict[str, Any]:
    data = _request("DELETE", "/api/bookmarks", json_body=ids)
    return data if isinstance(data, dict) else {"deleted": ids}


def list_tags() -> list[dict[str, Any]]:
    data = _request("GET", "/api/tags")
    if isinstance(data, list):
        return data
    raise ShioriError(f"Expected tag array, got {type(data).__name__}")


def rename_tag(tag_id: int, name: str) -> dict[str, Any]:
    data = _request("PUT", "/api/tags", json_body={"id": tag_id, "name": name})
    return data if isinstance(data, dict) else {"id": tag_id, "name": name}


def list_accounts() -> list[dict[str, Any]]:
    data = _request("GET", "/api/accounts")
    if isinstance(data, list):
        return data
    raise ShioriError(f"Expected account array, got {type(data).__name__}")
