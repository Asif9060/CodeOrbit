"""
Base settings for Quiz Platform project.
All environments inherit from this file.
"""
from pathlib import Path
from decouple import config

# ─── Paths ───────────────────────────────────────────────────────────────────
# Base dir is three levels up: config/settings/base.py → project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=lambda v: [s.strip() for s in v.split(",")])


# ─── Application Definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    # django-unfold must come BEFORE django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",

    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third-party
    "tailwind",
    "theme",

    # Project apps
    "apps.core",
    "apps.accounts",
    "apps.languages",
    "apps.learn",
    "apps.quizzes",
    "apps.results",
    "apps.leaderboard",
    "apps.contests",
    "apps.ai_solutions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ─── Database (MySQL) ─────────────────────────────────────────────────────────
DB_HOST = config("DB_HOST", default="")
DB_NAME = config("DB_NAME", default="")
DB_USER = config("DB_USER", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")
DB_PORT = config("DB_PORT", default="3306")
DB_SSL_CA = config("DB_SSL_CA", default="")


def _build_db_ssl_options():
    if not DB_SSL_CA:
        return None

    if "BEGIN CERTIFICATE" in DB_SSL_CA:
        ca_path = Path("/tmp/aiven-mysql-ca.pem")
        if not ca_path.exists():
            ca_path.write_text(DB_SSL_CA.strip() + "\n", encoding="utf-8")
        return {"ca": str(ca_path)}

    return {"ca": DB_SSL_CA}


if DB_HOST:
    ssl_options = _build_db_ssl_options()
    db_options = {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "isolation_level": "read committed",
        "charset": "utf8mb4",
    }
    if ssl_options:
        db_options["ssl"] = ssl_options

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "OPTIONS": db_options,
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "OPTIONS": {
                "read_default_file": str(BASE_DIR / "my.cnf"),
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "isolation_level": "read committed",
                "charset": "utf8mb4",
            },
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }


# ─── Authentication ───────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ─── Static & Media Files ─────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ─── Default Primary Key ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─── AI Provider Configuration ────────────────────────────────────────────────
# Change AI_ACTIVE_PROVIDER in .env to switch between providers instantly.
# Change the matching *_MODEL var to switch models without touching code.
AI_ACTIVE_PROVIDER = config("AI_ACTIVE_PROVIDER", default="ollama")

AI_PROVIDERS = {
    "ollama": {
        "base_url": config("OLLAMA_BASE_URL", default="http://localhost:11434"),
        "model": config("OLLAMA_MODEL", default="qwen3-coder:480b-cloud"),
    },
    "openai": {
        "api_key": config("OPENAI_API_KEY", default=""),
        "model": config("OPENAI_MODEL", default="gpt-4o"),
    },
    "gemini": {
        "api_key": config("GEMINI_API_KEY", default=""),
        "model": config("GEMINI_MODEL", default="gemini-1.5-pro"),
    },
    "anthropic": {
        "api_key": config("ANTHROPIC_API_KEY", default=""),
        "model": config("ANTHROPIC_MODEL", default="claude-3-5-sonnet-20241022"),
    },
}


# ─── Tailwind CSS ─────────────────────────────────────────────────────────────
TAILWIND_APP_NAME = "theme"
INTERNAL_IPS = ["127.0.0.1"]
# Windows: NPM_BIN_PATH = "npm.cmd" — set in development.py


# ─── django-unfold Admin ──────────────────────────────────────────────────────
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "CodeOrbit",
    "SITE_HEADER": "CodeOrbit Admin",
    "SITE_URL": "/",
    "SITE_ICON": None,
    "SITE_SYMBOL": "quiz",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "75 85 99",
            "default-dark": "209 213 219",
            "important-light": "17 24 39",
            "important-dark": "243 244 246",
        },
        "primary": {
            "50": "238 235 255",
            "100": "221 214 255",
            "200": "196 181 253",
            "300": "167 139 250",
            "400": "139 92 246",
            "500": "124 93 240",
            "600": "109 77 230",
            "700": "91 60 209",
            "800": "72 48 174",
            "900": "58 38 143",
            "950": "39 23 106",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": False,
                "items": [
                    {
                        "title": "Overview",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Languages",
                        "icon": "code",
                        "link": reverse_lazy("admin:languages_language_changelist"),
                    },
                    {
                        "title": "Topics",
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:learn_topic_changelist"),
                    },
                    {
                        "title": "Topic Progress",
                        "icon": "track_changes",
                        "link": reverse_lazy("admin:learn_topicprogress_changelist"),
                    },
                    {
                        "title": "Quizzes",
                        "icon": "quiz",
                        "link": reverse_lazy("admin:quizzes_quiz_changelist"),
                    },
                    {
                        "title": "Questions",
                        "icon": "help_outline",
                        "link": reverse_lazy("admin:quizzes_question_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Results",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_customuser_changelist"),
                    },
                    {
                        "title": "Results",
                        "icon": "leaderboard",
                        "link": reverse_lazy("admin:results_userresult_changelist"),
                    },
                ],
            },
            {
                "title": "Future Features",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Contests",
                        "icon": "emoji_events",
                        "link": reverse_lazy("admin:contests_contest_changelist"),
                    },
                    {
                        "title": "AI Explanations",
                        "icon": "auto_awesome",
                        "link": reverse_lazy("admin:ai_solutions_aiexplanation_changelist"),
                    },
                ],
            },
        ],
    },
}


# ─── Feature Flags ────────────────────────────────────────────────────────────
FEATURE_FLAGS = {
    "AI_EXPLANATIONS_ENABLED": config("FF_AI_EXPLANATIONS", default=False, cast=bool),
    "CONTESTS_ENABLED": config("FF_CONTESTS", default=False, cast=bool),
    "LEADERBOARD_ENABLED": config("FF_LEADERBOARD", default=True, cast=bool),
    "API_ENABLED": config("FF_API", default=False, cast=bool),
    "SOCIAL_LOGIN_ENABLED": config("FF_SOCIAL_LOGIN", default=False, cast=bool),
}
