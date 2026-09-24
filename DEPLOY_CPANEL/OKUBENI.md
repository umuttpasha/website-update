# TRAPCLUB - cPANEL KURULUM (ADIM ADIM, EN BASİT ANLATIM)

Bu dosyalari api.trapclub.net'in calistigi Python uygulamasinin klasorune koyacaksin.
Frontend (trapclub.net React sitesi) HIC etkilenmez.

============================================================
BOLUM 1 - HAZIRLIK (1 dakika)
============================================================
- Elinde su 8 dosya olacak (hepsi ayni klasorde):
  main.py, passenger_wsgi.py, admin.html, knowledge_base.md,
  announcements.json, requirements.txt, .env, KURULUM.md
- cPanel giris bilgilerin yaninda olsun.

============================================================
BOLUM 2 - PYTHON UYGULAMASINI BUL (Application root'u ogren)
============================================================
1. cPanel'e giris yap.
2. Arama kutusuna "Python" yaz.
3. "Setup Python App" (Python Uygulamasi Kur) yaz-tikla.
4. Acilan sayfada mevcut uygulamalar listelenir. api.trapclub.net olani bul.
5. O uygulamanin satirinda "Application root" yazan bir yol vardir.
   ORNEK: "api_trapclub" veya "apps/api" gibi. BU YOLU BIR KENARA NOT AL.
   (Dosyalari bu klasore koyacagiz.)
6. Ayrica sunlari kontrol et / not al:
   - "Application startup file"  -> passenger_wsgi.py OLMALI
   - "Application Entry point"    -> application OLMALI
   (Simdi degistirme, Bolum 5'te ayarlayacagiz.)

============================================================
BOLUM 3 - DOSYA YONETICISINI AC ve ESKI DOSYAYI YEDEKLE
============================================================
1. cPanel ana sayfaya don. Arama kutusuna "File" yaz.
2. "File Manager" (Dosya Yoneticisi) tikla.
3. Sol taraftan, Bolum 2'de not aldigin "Application root" klasorune git.
   (Ustteki adres cubuguna yolu yazip Enter'a da basabilirsin.)
4. Bu klasorde muhtemelen eski bir "main.py" gorursun.
   >>> ONEMLI YEDEK: main.py'ye SAG TIKLA -> "Copy" (Kopyala) ->
       hedef olarak ayni klasore "main_eski.py" yaz. Boylece yedegin olur.
   (Bir sey ters giderse main_eski.py'yi tekrar main.py yaparsin.)

============================================================
BOLUM 4 - 8 DOSYAYI YUKLE
============================================================
1. Ust menude "Upload" (Yukle) butonuna tikla.
2. Acilan sayfada 8 dosyayi tek tek (veya hepsini birden) secip yukle.
3. "main.py zaten var, uzerine yazilsin mi?" diye sorarsa -> EVET / Overwrite de.
   (Zaten yedegini main_eski.py olarak aldik.)
4. Yukleme bitince File Manager'a don, 8 dosyanin da orada oldugunu gor.

NOT: Klasordeki venv, tmp, public gibi diger seylere DOKUNMA. Sadece bu 8 dosya.

============================================================
BOLUM 5 - .env AYARLARINI DUZENLE (en onemli adim)
============================================================
1. File Manager'da ".env" dosyasina SAG TIKLA -> "Edit" (Duzenle).
   (Uyari cikarsa "Edit" de gec.)
2. Icinde su satirlar var. Sadece JWT_SECRET'i uzun rastgele bir sey yap:

   EMERGENT_LLM_KEY=sk-emergent-...        (AI anahtari - DOKUNMA)
   MC_SERVER_HOST=play.trapclub.net
   MC_SERVER_PORT=25567                    (sunucu offline gorunurse 25565 yap)
   AI_MODEL=gpt-5.6-terra
   CORS_ORIGINS=*
   JWT_SECRET=BURAYI_UZUN_RASTGELE_YAP     (<- ornek: kjf83hSk92mAqZ0pLx7... gibi)
   ADMIN_PASSWORD=TrapAdmin2026!           (admin sifresi - istersen degistir)
   MOD_PASSWORD=TrapMod2026!               (mod sifresi - istersen degistir)

3. Sag ustten "Save Changes" (Degisiklikleri Kaydet) tikla.

============================================================
BOLUM 6 - PAKETLERI KUR ve RESTART
============================================================
1. Tekrar "Setup Python App" sayfasina git, api.trapclub.net uygulamasini ac
   (kalem/edit ikonu).
2. Su iki alani kontrol et, degilse duzelt:
   - Application startup file: passenger_wsgi.py
   - Application Entry point:  application
   (Degistirdiysen "Save" de.)
3. Sayfada "Configuration files" bolumu vardir. Oraya "requirements.txt" yaz-ekle,
   sonra "Run Pip Install" butonuna bas. Kurulmasini bekle.
4. Eger "emergentintegrations" hatasi verirse: ayni sayfada "Enter to the virtual
   environment" diye bir komut gosterir (kopyala). cPanel'de "Terminal" ac, o komutu
   yapistir+Enter, sonra sunu yapistir+Enter:

   pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

5. En ustteki "Restart" butonuna bas.

============================================================
BOLUM 7 - CALISIYOR MU? TEST ET
============================================================
Tarayicini ac, sirayla su adresleri yaz:

1. https://api.trapclub.net/api/health
   -> {"status":"ok",...} gorursen API AYAKTA. :)

2. https://api.trapclub.net/api/server/status
   -> online true/false ve oyuncu sayisi gorursun.
      (offline ise .env'de portu 25565 yapip tekrar Restart et.)

3. https://api.trapclub.net/yonetim
   -> YONETIM PANELI acilir. Giris yap:
      admin / TrapAdmin2026!   (her seyi gorur)
      mod   / TrapMod2026!     (bilgi bankasi + duyurular)

4. Sitene gir (trapclub.net), AI asistana "Server IP nedir?" diye sor.
   -> Artik "play.trapclub.net" diye net cevap verir (eskisi gibi surekli Discord demez).

============================================================
BOLUM 8 - PANELI KULLANMA (api.trapclub.net/yonetim)
============================================================
- 📘 Bilgi Bankasi : AI'nin bildigi seyler. Duzenle -> "Kaydet & Yayinla".
                     AI aninda yeni bilgiyle cevap verir.
- 📣 Duyurular      : Ana sayfa duyurularini ekle / duzenle / sil.
- 👤 Yetkililer     : (sadece admin) yeni yetkili ekle / sil.
- 🕘 Aktivite       : (sadece admin) kim ne zaman girdi, ne degistirdi.

============================================================
BOLUM 9 - SORUN OLURSA
============================================================
- Uygulama acilmiyor / 500 hatasi:
  Setup Python App > uygulamanin "stderr.log" dosyasina bak. Genelde eksik paket
  veya yanlis startup file olur. (Bolum 6'yi tekrar yap.)
- Bir sey cok bozulursa: File Manager'da yeni main.py'yi sil, "main_eski.py"yi
  "main.py" yap, Restart et. Eski haline donersin.
- Sifre degistirmek: .env'de sifreyi degistir -> "staff_users.json" dosyasini SIL
  -> Restart. (Yeni sifreyle kendini yeniden olusturur.)
- Sunucu durumu hep offline: .env'de MC_SERVER_PORT'u 25567 -> 25565 dene. Hosting
  dis baglantiyi kisitliyorsa destege "Minecraft portuna outbound izni" de.

BITTI. Kolay gelsin. 💚
