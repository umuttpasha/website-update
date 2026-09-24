from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import json
import uuid
import socket
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
from mcstatus import JavaServer
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trapclub")

MC_HOST = os.environ.get('MC_SERVER_HOST', 'play.trapclub.net')
MC_PORT = int(os.environ.get('MC_SERVER_PORT', '25567'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
AI_MODEL = os.environ.get('AI_MODEL', 'gpt-5.6-terra')

KB_PATH = ROOT_DIR / 'knowledge_base.md'
ANN_PATH = ROOT_DIR / 'announcements.json'


def load_knowledge_base() -> str:
    try:
        return KB_PATH.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"knowledge_base.md okunamadi: {e}")
        return ""


def load_announcements():
    try:
        return json.loads(ANN_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning(f"announcements.json okunamadi: {e}")
        return []


def build_system_prompt() -> str:
    kb = load_knowledge_base()
    return (
        "Sen TrapClub Minecraft sunucusunun resmi AI asistanısın. "
        "Oyunculara Türkçe, samimi ve KISA cevaplar ver.\n\n"
        "KURALLAR:\n"
        "1. Önce aşağıdaki BİLGİ BANKASI'ndan cevap üret. Bilgi varsa doğrudan ve net cevapla, "
        "oyuncuyu gereksiz yere Discord'a yönlendirme.\n"
        "2. Sadece bilgi bankasında hiç bilgi yoksa ya da yetkili müdahalesi (ceza itirazı, ödeme "
        "sorunu, şikayet) gerekiyorsa Discord'a yönlendir: discord.gg/trapclub\n"
        "3. Bilgi bankasında olmayan şeyleri uydurma.\n"
        "4. Fiyat, IP, link gibi bilgileri net yaz. Cevapları kısa tut.\n\n"
        "=== BİLGİ BANKASI ===\n"
        f"{kb}\n"
        "=== BİLGİ BANKASI SONU ==="
    )


def resolve_ip(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host


app = FastAPI(title="TrapClub API")
api_router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@api_router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@api_router.get("/announcements")
async def announcements():
    return load_announcements()


@api_router.get("/server/status")
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


@api_router.post("/chat")
async def chat(req: ChatRequest):
    message = (req.message or "").strip()
    session_id = req.session_id or str(uuid.uuid4())

    async def event_stream():
        if not message:
            yield f'data: {json.dumps({"token": "Bir soru yazmalısın 🙂"})}\n\n'
            yield 'data: [DONE]\n\n'
            return
        if not EMERGENT_LLM_KEY:
            yield f'data: {json.dumps({"token": "AI şu an yapılandırılmadı. Discord: discord.gg/trapclub"})}\n\n'
            yield 'data: [DONE]\n\n'
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
            yield f'data: {json.dumps({"token": "Şu an yanıt veremedim, tekrar dener misin? Discord: discord.gg/trapclub"})}\n\n'
        yield 'data: [DONE]\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
