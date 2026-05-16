"""Unit tests for Shiori API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from shiori_mcp import client


@pytest.fixture(autouse=True)
def configure_client() -> None:
    client.configure(base_url="https://shiori.example", username="user", password="pass", session_id=None, timeout=5)


@respx.mock
def test_login_then_list_bookmarks() -> None:
    login = respx.post("https://shiori.example/api/login").mock(
        return_value=httpx.Response(200, json={"session": "sid-123", "account": {"id": 1, "username": "user"}})
    )
    bookmarks = respx.get("https://shiori.example/api/bookmarks").mock(
        return_value=httpx.Response(200, json={"bookmarks": [{"id": 1, "title": "One"}], "page": 1, "maxPage": 1})
    )

    assert client.list_bookmarks()["bookmarks"] == [{"id": 1, "title": "One"}]
    assert b'"username":"user"' in login.calls[0].request.content
    assert bookmarks.calls[0].request.headers["X-Session-Id"] == "sid-123"


@respx.mock
def test_session_id_skips_login_and_adds_bookmark_tag_objects() -> None:
    client.configure(base_url="https://shiori.example", session_id="existing")
    route = respx.post("https://shiori.example/api/bookmarks").mock(
        return_value=httpx.Response(200, json={"id": 7, "url": "https://example.com", "tags": [{"name": "ai"}]})
    )

    created = client.add_bookmark("https://example.com", tags="ai, research", public=True, create_archive=False)

    assert created["id"] == 7
    assert route.calls[0].request.headers["X-Session-Id"] == "existing"
    assert route.calls[0].request.content == b'{"url":"https://example.com","public":1,"createArchive":false,"tags":[{"name":"ai"},{"name":"research"}]}'


@respx.mock
def test_search_and_get_bookmark_are_client_side() -> None:
    client.configure(base_url="https://shiori.example", session_id="sid")
    respx.get("https://shiori.example/api/bookmarks").mock(
        return_value=httpx.Response(
            200,
            json={
                "bookmarks": [
                    {"id": 1, "title": "Python MCP", "url": "https://example.com/a", "excerpt": "tools", "tags": [{"name": "ai"}]},
                    {"id": 2, "title": "Cooking", "url": "https://example.com/b", "excerpt": "food", "tags": [{"name": "home"}]},
                ]
            },
        )
    )

    assert client.search_bookmarks(query="mcp", tag="ai")["bookmarks"][0]["id"] == 1
    assert client.get_bookmark(2)["title"] == "Cooking"
    assert client.get_bookmark_by_url("https://example.com/a")["id"] == 1
    with pytest.raises(client.ShioriError, match="not found"):
        client.get_bookmark(999)


@respx.mock
def test_update_delete_tags_accounts_and_health() -> None:
    client.configure(base_url="https://shiori.example", session_id="sid")
    respx.put("https://shiori.example/api/bookmarks").mock(return_value=httpx.Response(200, json={"id": 1, "title": "Updated"}))
    delete = respx.delete("https://shiori.example/api/bookmarks").mock(return_value=httpx.Response(204))
    respx.get("https://shiori.example/api/tags").mock(return_value=httpx.Response(200, json=[{"id": 1, "name": "ai", "nBookmarks": 2}]))
    rename = respx.put("https://shiori.example/api/tags").mock(return_value=httpx.Response(200, json={"id": 1, "name": "ml"}))
    respx.get("https://shiori.example/api/accounts").mock(return_value=httpx.Response(200, json=[{"id": 1, "username": "user", "owner": True}]))
    respx.get("https://shiori.example/api/bookmarks").mock(return_value=httpx.Response(200, json={"bookmarks": [{"id": 1}], "page": 1, "maxPage": 1}))

    assert client.update_bookmark({"id": 1, "title": "Updated"})["title"] == "Updated"
    assert client.delete_bookmarks([1, 2]) == {"ok": True}
    assert delete.calls[0].request.content == b"[1,2]"
    assert client.list_tags()[0]["name"] == "ai"
    assert client.rename_tag(1, "ml")["name"] == "ml"
    assert rename.calls[0].request.content == b'{"id":1,"name":"ml"}'
    assert client.list_accounts()[0]["username"] == "user"
    assert client.health_check()["ok"] is True


@respx.mock
def test_http_errors_are_readable() -> None:
    client.configure(base_url="https://shiori.example", session_id="sid")
    respx.get("https://shiori.example/api/tags").mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(client.ShioriError, match="HTTP 500"):
        client.list_tags()
