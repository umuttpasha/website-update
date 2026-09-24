# TrapClub API + Yetkili Paneli - cPanel Kurulum Rehberi (api.trapclub.net)

Bu paket, sitenin bozuk AI asistanini ve sunucu durumunu duzeltir; ayrica yetkililer icin
kurulum gerektirmeyen bir YONETIM PANELI ekler. Mevcut frontend'in kullandigi tum endpoint'leri
ayni formatta sunar.

## Endpoint'ler
Public:
- `GET  /api/health`
- `GET  /api/announcements`
- `GET  /api/server/status`
- `POST /api/chat`  (SSE: `data:{token}` ... `data:[DONE]`)

Yetkili (JWT Bearer):
- `POST   /api/auth/login`   {username,password} -> {access_token, user}
- `GET    /api/auth/me`
- `GET/PUT /api/admin/knowledge`               (bilgi bankasi)
- `POST/PUT/DELETE /api/admin/announcements`   (duyurular)

Panel (tarayicidan acilir):
- `https://api.trapclub.net/yonetim`  (veya `/admin`)

## Klasordeki Dosyalar (hepsini ayni klasore yukle)
- `main.py`             -> FastAPI uygulamasi
- `passenger_wsgi.py`   -> cPanel Passenger giris dosyasi
- `admin.html`          -> Yetkili paneli (tek dosya, kurulum gerekmez)
- `knowledge_base.md`   -> AI bilgi kaynagi
- `announcements.json`  -> Ana sayfa duyurulari
- `requirements.txt`    -> Python bagimliliklari
- `.env`                -> Ayarlar
- (`staff_users.json` ilk calismada OTOMATIK olusur - elle olusturma)

---

## Adim 1: Dosyalari Yukle
cPanel > File Manager ile `api.trapclub.net` uygulamasinin **Application root** klasorune
yukle. Eski `main.py`'nin yedegini al.

## Adim 2: Python App Ayarlari
cPanel > **Setup Python App**:
- **Startup file:** `passenger_wsgi.py`
- **Entry point:** `application`

## Adim 3: Bagimliliklari Kur
"Run Pip Install" ile `requirements.txt`. `emergentintegrations` kurulmazsa:
```
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Adim 4: .env
```
EMERGENT_LLM_KEY=...              # AI icin (verilen key)
MC_SERVER_HOST=play.trapclub.net
MC_SERVER_PORT=25567             # offline gorunurse 25565 dene
AI_MODEL=gpt-5.6-terra
CORS_ORIGINS=*
JWT_SECRET=...                    # UZUN, RASTGELE bir metin yaz (guvenlik icin sart!)
ADMIN_PASSWORD=TrapAdmin2026!    # admin hesabinin sifresi
MOD_PASSWORD=TrapMod2026!        # mod hesabinin sifresi
```
**ONEMLI:** `JWT_SECRET`'i mutlaka uzun rastgele bir metinle degistir.

## Adim 5: Restart

## Adim 6: Test
```
https://api.trapclub.net/api/health
https://api.trapclub.net/api/server/status
https://api.trapclub.net/yonetim      <- panel acilir
```
Panele giris:
- Kullanici: `admin`  Sifre: `TrapAdmin2026!`  (rol: admin)
- Kullanici: `mod`    Sifre: `TrapMod2026!`    (rol: mod)

## Panel Nasil Kullanilir
- **Bilgi Bankasi sekmesi:** Metni duzenle > "Kaydet & Yayinla". AI aninda yeni bilgiyle cevap verir.
- **Duyurular sekmesi:** Duyuru ekle / duzenle / sil. Ana sayfadaki Duyurular aninda guncellenir.

## Sifre Degistirme
1. `.env` icindeki `ADMIN_PASSWORD` / `MOD_PASSWORD` degerlerini degistir.
2. `staff_users.json` dosyasini SIL.
3. Uygulamayi Restart et (dosya yeni sifrelerle otomatik yeniden olusur).

## Sorun Giderme
- **500 / acilmiyor:** Setup Python App > **stderr.log**. Genelde eksik paket / yanlis startup file.
- **AI hala "yanit veremiyorum":** `.env` EMERGENT_LLM_KEY dogru mu, `emergentintegrations` kurulu mu?
- **server/status offline:** Once `MC_SERVER_PORT` (25567 -> 25565). Sunucu acik mi? Hosting outbound
  baglantiyi kisitliyor olabilir; destege Minecraft portuna cikis izni sor.
- **Panele giris "401":** kullanici/sifre .env ile uyumlu mu? Sifre degistirdiysen staff_users.json'i sil + Restart.

## Not: Frontend'e dokunmadan
Panel `admin.html` olarak backend'den servis edildigi icin mevcut React sitenizi yeniden
derlemeniz GEREKMEZ. Yetkililer dogrudan `api.trapclub.net/yonetim` adresini kullanir.
Istersen `admin.html`'i ana site koklasorune de koyup `trapclub.net/yonetim` yapabilirsin
(o durumda admin.html icindeki `const API = "/api"` satirini `"https://api.trapclub.net/api"` yap).
