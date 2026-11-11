import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-lava-shop-change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
# On Vercel set DEBUG=0

# Vercel sets VERCEL=1
ON_VERCEL = os.getenv("VERCEL") == "1"

allowed = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,.vercel.app")
ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]
if ON_VERCEL and ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://*.vercel.app,http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if o.strip()
]

LAVA_API_KEY = os.getenv("LAVA_API_KEY", "").strip()
LAVA_API_BASE = os.getenv("LAVA_API_BASE", "https://gate.lava.top").rstrip("/")
LAVA_OFFER_ID = os.getenv("LAVA_OFFER_ID", "").strip()
LAVA_CURRENCY = os.getenv("LAVA_CURRENCY", "RUB").strip().upper()

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.shop_nav",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

# SQLite: on Vercel filesystem is read-only except /tmp (data resets between cold starts)
if ON_VERCEL:
    db_path = Path("/tmp/lava_shop.sqlite3")
else:
    db_path = BASE_DIR / "db.sqlite3"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(db_path),
    }
}

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "shop" / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
