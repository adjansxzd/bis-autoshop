"""
Django settings for the BIS AutoShop backend.
Course project: Basics of Information Systems (INFT3107), KBTU.
"""
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Optional backend/.env file (KEY=value per line, git-ignored). Real environment variables win.
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _key, _value = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _value.strip())

# In production these come from environment variables. Never commit real secrets.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me-in-production-please")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # sign-out + refresh token rotation
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # our apps
    "accounts",
    "catalog",
    "orders",
    "inventory",
    "analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # picks EN/RU from the Accept-Language header the site sends
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # our admin branding
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite keeps the project easy to run on any laptop (also offline on exam day).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
# API messages in English or Russian. Our own texts: locale/ru/LC_MESSAGES/django.po (the compiled .mo is committed,
# so nobody needs gettext installed). Django, DRF and SimpleJWT already ship Russian translations.
LANGUAGES = [("en", "English"), ("ru", "Русский")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# Uploaded product photos
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
if len(sys.argv) > 1 and sys.argv[1] == "test":
    # tests write photos / 3D models into a temp folder, never into the real media/
    MEDIA_ROOT = Path(tempfile.gettempdir()) / "autoshop-test-media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Angular dev server runs on :4200 and calls the API on :8000
# "View site" link in the admin panel opens the shop
SHOP_URL = os.environ.get("SHOP_URL", "http://localhost:4200/")

# "Sign in with Google": OAuth client ID of our Google Cloud project "AutoShop" (autoshop-516008), see docs/GOOGLE_SIGN_IN.md.
# A client ID is public (it is sent to every browser), so it can live here; there is NO client secret in the code.
# Set GOOGLE_CLIENT_ID="" (environment or backend/.env) to switch the Google button off.
GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID", "427211189664-4b2dqvktgb0u58sf58402qeb5q74jv77.apps.googleusercontent.com"
)

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
).split(",")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # every refresh gives a NEW refresh token and the old one stops working (stolen tokens expire fast);
    # "Sign out" puts the refresh token on a blacklist (POST /api/auth/logout/)
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# ---------- Security (docs/SECURITY.md) ----------
RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"
# brute-force protection: at most 10 sign-in / registration attempts per minute from one IP
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"auth": "1000/min" if RUNNING_TESTS else os.environ.get("AUTH_RATE", "10/min")}
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ["rest_framework.throttling.ScopedRateThrottle"]  # only views with throttle_scope

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # JSON / form bodies; files are checked by their own validators

if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured

    if SECRET_KEY.startswith("dev-only"):
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in production (see .env.example).")
    if os.environ.get("HTTPS", "0") == "1":  # behind HTTPS on a real server
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SPECTACULAR_SETTINGS = {
    "TITLE": "BIS AutoShop API",
    "DESCRIPTION": "Online shop for auto parts and accessories: catalog, cart and order processing.",
    "VERSION": "0.1.0",
}
