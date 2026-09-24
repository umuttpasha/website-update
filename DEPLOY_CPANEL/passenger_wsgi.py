"""
cPanel Passenger giris dosyasi.
cPanel Python App WSGI kullanir; FastAPI ise ASGI'dir.
a2wsgi ile ASGI -> WSGI donusumu yapiyoruz.

Bu dosyayi application root'a 'passenger_wsgi.py' olarak koy.
"""
from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)
