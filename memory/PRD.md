# TrapClub — Backend Hızlı Düzeltme (PRD)

## Orijinal Problem
Mevcut canlı TrapClub sitesinde (React frontend zaten yayında, FastAPI backend api.trapclub.net)
iki şey bozuktu: (1) canlı sunucu durumu offline görünüyordu, (2) AI asistan her soruya
"Şu an yanıt veremiyorum, Discord'dan ulaş" diyordu. Hedef: cPanel'e yapıştırılacak hazır,
çalışan bir backend sürümü çıkarmak. Tam refactor değil, hızlı düzeltme.

## Kullanıcı Kararları
- AI modeli: OpenAI **gpt-5.6-terra** (Emergent Universal Key ile)
- Minecraft sunucu: play.trapclub.net:25567
- Bilgi kaynağı: dosya tabanlı (`knowledge_base.md`)
- Dil: Türkçe

## Tespit Edilen Gerçek Prod Sözleşmesi (api.trapclub.net)
- `GET /api/health` → {status, timestamp}
- `GET /api/announcements` → [{id,title,tag,body,image,author,created_at,updated_at}]
- `GET /api/server/status` → {ip, online, players, max_players, version, motd, checked_at}
- `POST /api/chat` → **SSE** stream, body {message, session_id}, cevap `data:{token}` ... `data:[DONE]`

## Mimari / Yapılanlar (2026-06)
- Backend (`/app/backend/server.py`) gerçek sözleşmeye birebir uyacak şekilde yeniden yazıldı.
  - `mcstatus` ile async Minecraft sorgusu (asyncio.wait_for ile 4s sert timeout → takılma yok).
  - AI chat: `emergentintegrations` `LlmChat.stream_message` + gpt-5.6-terra, SSE token akışı.
  - Sistem promptu `knowledge_base.md`'yi gömüyor; ÖNCE bilgi bankasından cevap, yoksa Discord.
  - Duyurular `announcements.json`'dan (mevcut 3 duyuru korunarak).
- Bilgi bankası gerçek verilerle dolduruldu: VIP (₺75/₺149/₺299), 4 kural, turnuva (Pazar 20:00,
  10.000 TL), yetkililer, ban itiraz süreci, sunucuya giriş, SSS.
- cPanel drop-in paketi: `/app/DEPLOY_CPANEL/` (main.py, passenger_wsgi.py, requirements.txt,
  knowledge_base.md, announcements.json, .env, KURULUM.md).
- Emergent ortamında demo React arayüzü (durum kartı + duyurular + SSE chat) — test/doğrulama için.

## Test Durumu
- testing_agent iteration_1: backend 6/6, frontend 3/3 PASS. Bilinen bug yok.
- Not: Bu sandbox'tan Minecraft sunucusuna ağ erişimi olmadığı için `online:false` — bu beklenen.
  Gerçek cPanel sunucusunda doğru port ile online/oyuncu sayısı dönecektir.

## Yetkili Paneli (2026-06 — eklendi)
- JWT (PyJWT HS256) + bcrypt, **dosya tabanlı çoklu hesap** (`staff_users.json`, otomatik seed) — DB yok.
- Endpoint'ler: `/api/auth/login`, `/api/auth/me`, `/api/admin/knowledge` (GET/PUT),
  `/api/admin/announcements` (POST/PUT/DELETE). Tümü Bearer token korumalı.
- Varsayılan hesaplar: admin/TrapAdmin2026!, mod/TrapMod2026! (`.env`'den değiştirilebilir).
- Panel: Emergent demo'da React `/yonetim`; cPanel'de kurulum gerektirmeyen tek dosya `admin.html`
  (`api.trapclub.net/yonetim` olarak backend'den servis edilir). Frontend rebuild gerekmez.
- Yetkililer bilgi bankasını ve duyuruları siteden düzenleyip anında yayınlar.
- **Yetkili Yönetimi (admin-only):** `require_admin` + `/api/admin/staff` GET/POST/DELETE. Admin panelden
  yetkili ekler/siler (kendini ve son admin'i silemez, çift kullanıcı 409). "Yetkililer" sekmesi
  yalnızca admin rolüne görünür. Test: iteration_3 → backend 10/10, frontend %100.
- Test: iteration_2 → backend 15/15, frontend tüm akışlar PASS.

## Backlog / Sonraki
- P1: server/status için birkaç saniyelik cache (burst trafikte MC sorgusunu azaltmak).
- P2: CORS'u production'da trapclub.net'e sabitlemek.
- P2: knowledge_base'i modül yüklemede cache'lemek (her istekte IO yerine).
- P2: Duyuruları admin panelinden yönetmek (şu an dosya tabanlı).
