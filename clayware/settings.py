"""
Django settings for ClayWare
Django 6.0.5
"""

from pathlib import Path
from datetime import timedelta
import os

from decouple import config


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = config("SECRET_KEY")

DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool
)


ALLOWED_HOSTS = [
    "claywarebackendapis.onrender.com",
    "127.0.0.1",
    "localhost",
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third party
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework.authtoken",

    # ClayWare
    "accounts",
    "seller",
    "User",
    "adminMain",
    "deliverypatner",
    "orders",
    "Marketing",
    "payments",
    "product_reviews",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL
# ============================================================

ROOT_URLCONF = "clayware.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

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


# ============================================================
# WSGI / ASGI
# ============================================================

WSGI_APPLICATION = "clayware.wsgi.application"

ASGI_APPLICATION = "clayware.asgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASES = {

    "default": {

        "ENGINE":
            "django.db.backends.sqlite3",

        "NAME":
            BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# CUSTOM USER
# ============================================================

AUTH_USER_MODEL = "accounts.CustomUser"


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


STATICFILES_DIRS = [

    BASE_DIR / "static",
]


STORAGES = {

    "default": {

        "BACKEND":
            "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {

        "BACKEND":
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# CORS
# ============================================================

CORS_ALLOWED_ORIGINS = [

    # Local
    "http://localhost:5173",
    "http://localhost:5174",

    # Customer
    "https://clayware-frontend.vercel.app",

    # Seller
    "https://claywares-seller-portal.vercel.app",

    # Reviewer
    "https://claywareproductreviewer.vercel.app",
]


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [

    "https://clayware-frontend.vercel.app",

    "https://claywares-seller-portal.vercel.app",

    "https://claywareproductreviewer.vercel.app",

    "https://claywarebackendapis.onrender.com",
]


# ============================================================
# DRF
# ============================================================

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": [

        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [

        "rest_framework.permissions.IsAuthenticated",
    ],

    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",

    "PAGE_SIZE": 20,

    "DEFAULT_THROTTLE_CLASSES": [

        "rest_framework.throttling.AnonRateThrottle",

        "rest_framework.throttling.UserRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {

        "anon": "100/min",

        "user": "300/min",
    },
}


# ============================================================
# JWT
# ============================================================

SIMPLE_JWT = {

    "ACCESS_TOKEN_LIFETIME":
        timedelta(minutes=30),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(days=7),

    "ROTATE_REFRESH_TOKENS":
        True,

    "BLACKLIST_AFTER_ROTATION":
        True,

    "UPDATE_LAST_LOGIN":
        True,

    "AUTH_HEADER_TYPES":
        ("Bearer",),

    "AUTH_HEADER_NAME":
        "HTTP_AUTHORIZATION",
}


# ============================================================
# RAZORPAY
# ============================================================

RAZORPAY_KEY_ID = config(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = config(
    "RAZORPAY_KEY_SECRET"
)

RAZORPAY_CURRENCY = config(
    "RAZORPAY_CURRENCY",
    default="INR"
)


# ============================================================
# TWILIO
# ============================================================

TWILIO_ACCOUNT_SID = config(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = config(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_VERIFY_SERVICE_SID = config(
    "TWILIO_VERIFY_SERVICE_SID"
)


# ============================================================
# CACHE
# ============================================================

CACHES = {

    "default": {

        "BACKEND":
            "django.core.cache.backends.locmem.LocMemCache",

        "LOCATION":
            "clayware-cache",
    }
}


# ============================================================
# PRODUCTION SECURITY
# ============================================================

if not DEBUG:

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)