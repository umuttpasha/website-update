# TrapClub API - cPanel Kurulum Rehberi (api.trapclub.net)

Bu klasordeki dosyalar, sitenin bozuk olan AI asistanini ve sunucu durumunu duzeltir.
Mevcut frontend'in kullandigi TUM endpoint'leri ayni formatta sunan TAM (drop-in) surumdur.

## Endpoint'ler (frontend'in bekledigi format)
- `GET  /api/health`        -> {"status":"ok","timestamp":...}
- `GET  /api/announcements` -> duyurular listesi (announcements.json'dan)
- `GET  /api/server/status` -> {ip, online, players, max_players, version, motd, checked_at}
- `POST /api/chat`          -> SSE stream. Istek: {"message","session_id"}
                               Cevap: `data: {"token":"..."}` ... `data: [DONE]`

## Klasordeki Dosyalar
- `main.py`             -> FastAPI uygulamasi (tum route'lar)
- `passenger_wsgi.py`   -> cPanel Passenger giris dosyasi
- `knowledge_base.md`   -> AI'nin bilgi kaynagi (istedigin gibi duzenle)
- `announcements.json`  -> Ana sayfadaki Duyurular (istedigin gibi duzenle)
- `requirements.txt`    -> Python bagimliliklari
- `.env`                -> Ayarlar (LLM key, sunucu IP/port, model)

---

## Adim 1: Dosyalari Yukle
cPanel > File Manager ile, `api.trapclub.net` uygulamasinin **Application root**
klasorune bu 6 dosyayi (ayni klasore) yukle. Eski `main.py`'nin yedegini almayi unutma.

## Adim 2: Python App Ayarlari
cPanel > **Setup Python App** > uygulamani sec:
- **Application startup file:** `passenger_wsgi.py`
- **Application Entry point:** `application`
- **Application root / URL:** mevcut api.trapclub.net ayarlari (degistirme)

## Adim 3: Bagimliliklari Kur
"Run Pip Install" ile `requirements.txt`'i kur. Eger `emergentintegrations`
normal pip ile kurulmazsa, uygulamanin virtualenv'inde su komutu calistir:
```
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Adim 4: .env Kontrolu
```
EMERGENT_LLM_KEY=...              # AI icin gerekli (verilen key)
MC_SERVER_HOST=play.trapclub.net
MC_SERVER_PORT=25567             # sunucu hala offline gorunuyorsa 25565 dene
AI_MODEL=gpt-5.6-terra
CORS_ORIGINS=*                    # istersen https://trapclub.net yazabilirsin
```

## Adim 5: Restart
Setup Python App sayfasinda **Restart** butonuna bas.

## Adim 6: Test
Tarayicidan:
```
https://api.trapclub.net/api/health          -> {"status":"ok",...}
https://api.trapclub.net/api/server/status   -> online/oyuncu sayisi
https://api.trapclub.net/api/announcements   -> duyurular
```
AI testi (terminal):
```
curl -N -X POST https://api.trapclub.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Server IP nedir?","session_id":"test-1"}'
```
`data: {"token":"..."}` satirlari ve sonunda `data: [DONE]` gormelisin.

## Sorun Giderme
- **500 / acilmiyor:** Setup Python App > uygulamanin **stderr.log**'una bak.
  Genelde eksik paket ya da yanlis startup file.
- **AI hala "yanit veremiyorum" diyor:** `.env` icindeki EMERGENT_LLM_KEY dogru mu ve
  `emergentintegrations` kurulu mu kontrol et. stderr.log'da "AI chat hatasi" ariyor.
- **server/status hep offline:** Once MC_SERVER_PORT'u kontrol et (25567 -> 25565 dene).
  Sunucu gercekten acik mi bak. Bazi hostingler dis baglantiyi kisitlar; o durumda hosting
  destegine Minecraft portuna cikis (outbound) izni sor.

## Icerik Guncelleme (kod bilmeden)
- AI'nin bildigi seyleri degistirmek: `knowledge_base.md`'yi duzenle, kaydet, Restart.
- Ana sayfadaki duyurulari degistirmek: `announcements.json`'i duzenle, kaydet, Restart.
