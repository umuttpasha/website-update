"""
TrapClub FastAPI Backend - api.trapclub.net icin TAM (drop-in) surum + Yetkili Paneli.

Public:
  GET  /api/health
  GET  /api/announcements
  GET  /api/server/status
  POST /api/chat            (SSE stream)
Yetkili (JWT Bearer):
  POST   /api/auth/login    {username,password} -> {access_token, user}
  GET    /api/auth/me
  GET    /api/admin/knowledge
  PUT    /api/admin/knowledge            {content}
  POST   /api/admin/announcements        {title,tag,body,image?}
  PUT    /api/admin/announcements/{id}
  DELETE /api/admin/announcements/{id}

Ayni klasorde bulunmasi gerekenler: knowledge_base.md, announcements.json
(staff_users.json ilk calismada otomatik olusur).
"""
import os
import json
import uuid
import socket
import asyncio
import logging
import bcrypt
import jwt
from pathlib import Path
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from mcstatus import JavaServer
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trapclub")

MC_HOST = os.environ.get("MC_SERVER_HOST", "play.trapclub.net")
MC_PORT = int(os.environ.get("MC_SERVER_PORT", "25567"))
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-5.6-terra")
JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-secret")
JWT_ALG = "HS256"
TOKEN_HOURS = 12

KB_PATH = ROOT_DIR / "knowledge_base.md"
ANN_PATH = ROOT_DIR / "announcements.json"
STAFF_PATH = ROOT_DIR / "staff_users.json"
ADMIN_HTML = ROOT_DIR / "admin.html"


# ---------- Data helpers ----------
def load_knowledge_base() -> str:
    try:
        return KB_PATH.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"knowledge_base.md okunamadi: {e}")
        return ""


def save_knowledge_base(content: str):
    KB_PATH.write_text(content, encoding="utf-8")


def load_announcements():
    try:
        return json.loads(ANN_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"announcements.json okunamadi: {e}")
        return []


def save_announcements(items):
    ANN_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def build_system_prompt() -> str:
    kb = load_knowledge_base()
    return (
        "Sen TrapClub Minecraft sunucusunun resmi AI asistanisin. "
        "Oyunculara Turkce, samimi ve KISA cevaplar ver.\n\n"
        "KURALLAR:\n"
        "1. Once asagidaki BILGI BANKASI'ndan cevap uret. Bilgi varsa dogrudan ve net cevapla, "
        "oyuncuyu gereksiz yere Discord'a yonlendirme.\n"
        "2. Sadece bilgi bankasinda hic bilgi yoksa ya da yetkili mudahalesi (ceza itirazi, odeme "
        "sorunu, sikayet) gerekiyorsa Discord'a yonlendir: discord.gg/trapclub\n"
        "3. Bilgi bankasinda olmayan seyleri uydurma.\n"
        "4. Fiyat, IP, link gibi bilgileri net yaz. Cevaplari kisa tut.\n\n"
        "=== BILGI BANKASI ===\n"
        f"{kb}\n"
        "=== BILGI BANKASI SONU ==="
    )


def resolve_ip(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host


# ---------- Auth helpers ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def load_staff():
    try:
        return json.loads(STAFF_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_staff(users):
    STAFF_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def seed_staff():
    if STAFF_PATH.exists():
        return
    defaults = [
        {"username": "admin", "password": os.environ.get("ADMIN_PASSWORD", "TrapAdmin2026!"), "role": "admin"},
        {"username": "mod", "password": os.environ.get("MOD_PASSWORD", "TrapMod2026!"), "role": "mod"},
    ]
    users = [{"username": d["username"], "password_hash": hash_password(d["password"]), "role": d["role"]}
             for d in defaults]
    save_staff(users)
    logger.info("staff_users.json olusturuldu (varsayilan hesaplar).")


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Yetkisiz erisim")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum suresi doldu, tekrar giris yap")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Gecersiz oturum")
    users = load_staff()
    u = next((x for x in users if x["username"] == payload.get("sub")), None)
    if not u:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi")
    return {"username": u["username"], "role": u["role"]}


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu islem icin admin yetkisi gerekli")
    return user


seed_staff()

app = FastAPI(title="TrapClub API")
router = APIRouter()


# Yetkili paneli (tek dosyalik HTML) - api.trapclub.net/yonetim
@app.get("/yonetim", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    try:
        return HTMLResponse(ADMIN_HTML.read_text(encoding="utf-8"))
    except Exception:
        return HTMLResponse("<h1>admin.html bulunamadi</h1>", status_code=404)


# ---------- Models ----------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class KnowledgeUpdate(BaseModel):
    content: str


class AnnouncementIn(BaseModel):
    title: str
    tag: str
    body: str
    image: Optional[str] = None


class StaffIn(BaseModel):
    username: str
    password: str
    role: str = "mod"


# ---------- Public ----------
@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/announcements")
async def announcements():
    return load_announcements()


@router.get("/server/status")
async def server_status():
    result = {
        "ip": resolve_ip(MC_HOST),
        "online": False,
        "players": 0,
        "max_players": 0,
        "version": None,
        "motd": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async def _query():
            server = await JavaServer.async_lookup(f"{MC_HOST}:{MC_PORT}", timeout=3)
            return await server.async_status(tries=1)

        status = await asyncio.wait_for(_query(), timeout=4)
        result["online"] = True
        result["players"] = status.players.online
        result["max_players"] = status.players.max
        result["version"] = status.version.name
        result["motd"] = status.description if isinstance(status.description, str) else str(status.description)
    except Exception as e:
        logger.warning(f"Minecraft sorgusu basarisiz: {e}")
    return result


@router.post("/chat")
async def chat(req: ChatRequest):
    message = (req.message or "").strip()
    session_id = req.session_id or str(uuid.uuid4())

    async def event_stream():
        if not message:
            yield f'data: {json.dumps({"token": "Bir soru yazmalisin."})}\n\n'
            yield "data: [DONE]\n\n"
            return
        if not EMERGENT_LLM_KEY:
            yield f'data: {json.dumps({"token": "AI su an yapilandirilmadi. Discord: discord.gg/trapclub"})}\n\n'
            yield "data: [DONE]\n\n"
            return
        try:
            llm = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=build_system_prompt(),
            ).with_model("openai", AI_MODEL)
            async for event in llm.stream_message(UserMessage(text=message)):
                if isinstance(event, TextDelta):
                    if event.content:
                        yield f'data: {json.dumps({"token": event.content})}\n\n'
                elif isinstance(event, StreamDone):
                    break
        except Exception as e:
            logger.error(f"AI chat hatasi: {e}")
            yield f'data: {json.dumps({"token": "Su an yanit veremedim, tekrar dener misin? Discord: discord.gg/trapclub"})}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------- Auth ----------
@router.post("/auth/login")
async def login(req: LoginRequest):
    users = load_staff()
    u = next((x for x in users if x["username"].lower() == req.username.strip().lower()), None)
    if not u or not verify_password(req.password, u["password_hash"]):
        raise HTTPException(status_code=401, detail="Kullanici adi veya sifre hatali")
    token = create_token(u["username"], u["role"])
    return {"access_token": token, "token_type": "bearer", "user": {"username": u["username"], "role": u["role"]}}


@router.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return user


# ---------- Admin (protected) ----------
@router.get("/admin/knowledge")
async def get_knowledge(user=Depends(get_current_user)):
    return {"content": load_knowledge_base()}


@router.put("/admin/knowledge")
async def update_knowledge(payload: KnowledgeUpdate, user=Depends(get_current_user)):
    save_knowledge_base(payload.content)
    return {"ok": True, "message": "Bilgi bankasi guncellendi"}


@router.post("/admin/announcements")
async def create_announcement(payload: AnnouncementIn, user=Depends(get_current_user)):
    items = load_announcements()
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "tag": payload.tag,
        "body": payload.body,
        "image": payload.image,
        "author": user["username"],
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_announcements(items)
    return item


@router.put("/admin/announcements/{ann_id}")
async def update_announcement(ann_id: str, payload: AnnouncementIn, user=Depends(get_current_user)):
    items = load_announcements()
    item = next((x for x in items if x["id"] == ann_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Duyuru bulunamadi")
    item.update({
        "title": payload.title,
        "tag": payload.tag,
        "body": payload.body,
        "image": payload.image,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    save_announcements(items)
    return item


@router.delete("/admin/announcements/{ann_id}")
async def delete_announcement(ann_id: str, user=Depends(get_current_user)):
    items = load_announcements()
    new_items = [x for x in items if x["id"] != ann_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Duyuru bulunamadi")
    save_announcements(new_items)
    return {"ok": True}


# ---------- Staff management (admin only) ----------
@router.get("/admin/staff")
async def list_staff(user=Depends(require_admin)):
    return [{"username": u["username"], "role": u["role"]} for u in load_staff()]


@router.post("/admin/staff")
async def create_staff(payload: StaffIn, user=Depends(require_admin)):
    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(status_code=400, detail="Kullanici adi ve sifre zorunlu")
    if payload.role not in ("admin", "mod"):
        raise HTTPException(status_code=400, detail="Rol 'admin' veya 'mod' olmali")
    users = load_staff()
    if any(u["username"].lower() == username.lower() for u in users):
        raise HTTPException(status_code=409, detail="Bu kullanici adi zaten var")
    users.append({"username": username, "password_hash": hash_password(payload.password), "role": payload.role})
    save_staff(users)
    return {"username": username, "role": payload.role}


@router.delete("/admin/staff/{username}")
async def delete_staff(username: str, user=Depends(require_admin)):
    if username.lower() == user["username"].lower():
        raise HTTPException(status_code=400, detail="Kendi hesabini silemezsin")
    users = load_staff()
    target = next((u for u in users if u["username"].lower() == username.lower()), None)
    if not target:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi")
    if target["role"] == "admin" and sum(1 for u in users if u["role"] == "admin") <= 1:
        raise HTTPException(status_code=400, detail="Son admin hesabi silinemez")
    users = [u for u in users if u["username"].lower() != username.lower()]
    save_staff(users)
    return {"ok": True}


# Frontend /api altini cagiriyor; kok dizini de guvenlik icin ekliyoruz.
app.include_router(router, prefix="/api")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
