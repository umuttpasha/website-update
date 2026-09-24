"""TrapClub backend regression tests."""
import json
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://trapai-repair.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


# -------- /api/health --------
def test_health_shape():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert isinstance(data.get("timestamp"), str)
    # ISO8601 sanity check
    assert "T" in data["timestamp"]


# -------- /api/announcements --------
def test_announcements_shape():
    r = requests.get(f"{API}/announcements", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 3
    required = {"id", "title", "tag", "body", "image", "author", "created_at", "updated_at"}
    for item in data:
        assert required.issubset(item.keys()), f"missing keys: {required - item.keys()}"
    assert "Sezon 4" in data[0]["title"]


# -------- /api/server/status --------
def test_server_status_shape_and_speed():
    start = time.time()
    r = requests.get(f"{API}/server/status", timeout=10)
    elapsed = time.time() - start
    assert r.status_code == 200
    data = r.json()
    required = {"ip", "online", "players", "max_players", "version", "motd", "checked_at"}
    assert required.issubset(data.keys())
    assert isinstance(data["online"], bool)
    assert isinstance(data["players"], int)
    assert isinstance(data["max_players"], int)
    assert elapsed < 8, f"status endpoint too slow: {elapsed}s"


# -------- SSE chat helper --------
def _consume_sse(message, session_id, timeout=90):
    tokens = []
    saw_done = False
    with requests.post(
        f"{API}/chat",
        json={"message": message, "session_id": session_id},
        stream=True,
        timeout=timeout,
    ) as r:
        assert r.status_code == 200, r.text
        ctype = r.headers.get("content-type", "")
        assert "text/event-stream" in ctype, f"bad content-type: {ctype}"
        for raw in r.iter_lines(decode_unicode=True):
            if not raw:
                continue
            if not raw.startswith("data:"):
                continue
            payload = raw[len("data:"):].strip()
            if payload == "[DONE]":
                saw_done = True
                break
            try:
                obj = json.loads(payload)
            except Exception:
                continue
            tok = obj.get("token")
            if tok:
                tokens.append(tok)
    return "".join(tokens), saw_done


def test_chat_server_ip():
    text, done = _consume_sse("Server IP nedir?", "test-1")
    assert done, "SSE did not terminate with [DONE]"
    assert text.strip(), "empty answer"
    assert "play.trapclub.net" in text.lower() or "play.trapclub.net" in text


def test_chat_vip_prices():
    text, done = _consume_sse("VIP fiyatları ne?", "test-2")
    assert done
    for price in ("75", "149", "299"):
        assert price in text, f"price {price} missing. answer={text!r}"


def test_chat_ban_directs_to_discord():
    text, done = _consume_sse("Ban yedim ne yapmalıyım?", "test-3")
    assert done
    low = text.lower()
    assert "discord" in low


# -------- Auth --------
ADMIN_USER = "admin"
ADMIN_PASS = "TrapAdmin2026!"
MOD_USER = "mod"
MOD_PASS = "TrapMod2026!"


def _login(username, password):
    return requests.post(f"{API}/auth/login", json={"username": username, "password": password}, timeout=10)


@pytest.fixture(scope="module")
def admin_token():
    r = _login(ADMIN_USER, ADMIN_PASS)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_login_admin_ok():
    r = _login(ADMIN_USER, ADMIN_PASS)
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d.get("access_token"), str) and len(d["access_token"]) > 20
    assert d["user"]["username"] == "admin"
    assert d["user"]["role"] == "admin"


def test_login_mod_ok():
    r = _login(MOD_USER, MOD_PASS)
    assert r.status_code == 200
    d = r.json()
    assert d["user"]["role"] == "mod"


def test_login_wrong_password():
    r = _login(ADMIN_USER, "wrong")
    assert r.status_code == 401


def test_me_requires_token():
    r = requests.get(f"{API}/auth/me", timeout=10)
    assert r.status_code == 401


def test_me_with_token(admin_headers):
    r = requests.get(f"{API}/auth/me", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["username"] == "admin" and d["role"] == "admin"


# -------- Admin protection --------
def test_admin_endpoints_require_auth():
    assert requests.get(f"{API}/admin/knowledge", timeout=10).status_code == 401
    assert requests.put(f"{API}/admin/knowledge", json={"content": "x"}, timeout=10).status_code == 401
    assert requests.post(f"{API}/admin/announcements", json={"title": "t", "tag": "t", "body": "b"}, timeout=10).status_code == 401
    assert requests.put(f"{API}/admin/announcements/xxx", json={"title": "t", "tag": "t", "body": "b"}, timeout=10).status_code == 401
    assert requests.delete(f"{API}/admin/announcements/xxx", timeout=10).status_code == 401


# -------- Knowledge base (round-trip, restore original) --------
def test_knowledge_get_put_restore(admin_headers):
    r = requests.get(f"{API}/admin/knowledge", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    original = r.json()["content"]
    assert isinstance(original, str) and len(original) > 0

    test_marker = "\n\n<!-- TEST_MARKER_DO_NOT_KEEP -->\n"
    new_content = original + test_marker
    try:
        put = requests.put(f"{API}/admin/knowledge", json={"content": new_content}, headers=admin_headers, timeout=10)
        assert put.status_code == 200
        assert put.json().get("ok") is True

        got = requests.get(f"{API}/admin/knowledge", headers=admin_headers, timeout=10)
        assert got.status_code == 200
        assert test_marker in got.json()["content"]
    finally:
        # Restore original
        restore = requests.put(f"{API}/admin/knowledge", json={"content": original}, headers=admin_headers, timeout=10)
        assert restore.status_code == 200
        after = requests.get(f"{API}/admin/knowledge", headers=admin_headers, timeout=10)
        assert after.json()["content"] == original


# -------- Announcements CRUD (cleanup after) --------
def test_announcements_crud(admin_headers):
    before = requests.get(f"{API}/announcements", timeout=10).json()
    before_count = len(before)

    payload = {"title": "TEST_ANN", "tag": "TestTag", "body": "test body"}
    c = requests.post(f"{API}/admin/announcements", json=payload, headers=admin_headers, timeout=10)
    assert c.status_code == 200
    created = c.json()
    ann_id = created["id"]
    try:
        assert created["author"] == "admin"
        assert created["title"] == "TEST_ANN"
        assert "created_at" in created

        pub = requests.get(f"{API}/announcements", timeout=10).json()
        assert any(a["id"] == ann_id for a in pub)
        assert len(pub) == before_count + 1

        upd = requests.put(
            f"{API}/admin/announcements/{ann_id}",
            json={"title": "TEST_ANN_2", "tag": "TestTag", "body": "updated"},
            headers=admin_headers, timeout=10,
        )
        assert upd.status_code == 200
        assert upd.json()["title"] == "TEST_ANN_2"

        pub2 = requests.get(f"{API}/announcements", timeout=10).json()
        item = next(a for a in pub2 if a["id"] == ann_id)
        assert item["title"] == "TEST_ANN_2"
        assert item["body"] == "updated"
    finally:
        d = requests.delete(f"{API}/admin/announcements/{ann_id}", headers=admin_headers, timeout=10)
        assert d.status_code == 200

    after = requests.get(f"{API}/announcements", timeout=10).json()
    assert len(after) == before_count
    assert not any(a["id"] == ann_id for a in after)


def test_announcements_still_original_three():
    r = requests.get(f"{API}/announcements", timeout=10)
    data = r.json()
    assert len(data) == 3
    tags = {a["tag"] for a in data}
    assert {"Trap PvP", "Turnuva", "Güncelleme"}.issubset(tags)
