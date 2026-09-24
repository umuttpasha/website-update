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
