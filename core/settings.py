"""
Django settings for core project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    """Read a boolean from the environment ('1'/'true'/'yes'/'on' => True)."""
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    """Read a comma-separated list from the environment."""
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
# The fallback below is the ORIGINAL committed key and must be considered
# COMPROMISED (it lives in git history). Set DJANGO_SECRET_KEY in the
# environment for any real deployment and rotate it. See .env.example.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-6c49h$%0zbghaapjzoqd5fehy7n1#+vgnv)t*8t&tveeduc_9t',
)

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False; set DJANGO_DEBUG=1 locally for development.
DEBUG = env_bool('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = env_list(
    'DJANGO_ALLOWED_HOSTS',
    'gonut.click,www.gonut.click,localhost,127.0.0.1',
)

CSRF_TRUSTED_ORIGINS = env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'https://gonut.click,https://www.gonut.click',
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'videos',
    'accounts',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files efficiently even when DEBUG=False,
    # so the site keeps working in production without a separate web server.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'videos.context_processors.categories_processor',
                'core.context_processors.seo_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database - SQLite for now, will migrate to PostgreSQL later
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL configuration (for later migration)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'your_db_name',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: compress static files (no manifest, so a missing referenced
# file never crashes a page) and serve straight from the finders, which means
# the site works whether or not `collectstatic` has been run.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
WHITENOISE_USE_FINDERS = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'videos:home'
LOGOUT_REDIRECT_URL = 'videos:home'

# =============================================================================
# Session Configuration (Remember Me)
# =============================================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Store sessions in database
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # Default: 30 days (in seconds)
SESSION_COOKIE_SECURE = not DEBUG  # Only send cookie over HTTPS in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_DOMAIN = '.gonut.click' if not DEBUG else None  # Share session across subdomains
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session expiry on every request

# CSRF Cookie settings (must match session for consistency)
CSRF_COOKIE_SECURE = not DEBUG  # Only send CSRF cookie over HTTPS in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = '.gonut.click' if not DEBUG else None  # Share CSRF across subdomains

# =============================================================================
# Security Hardening
# =============================================================================
# Trust the X-Forwarded-Proto header from the front-end proxy/load balancer so
# Django knows the original request was HTTPS (prevents redirect loops).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Don't let browsers MIME-sniff responses away from the declared content-type.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Limit referrer leakage to other origins.
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# No one may frame our pages (clickjacking protection). We embed *other* sites
# in iframes on our watch pages, which this setting does not affect.
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    # Redirect all HTTP to HTTPS (toggle off via env if the proxy already does it).
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', default=True)

    # HTTP Strict Transport Security — tell browsers to always use HTTPS.
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', 31536000))  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# SEO & Site Configuration
# =============================================================================
SITE_NAME = 'goNuts'
SITE_DOMAIN = 'gonut.click'
SITE_URL = 'https://gonut.click'
SITE_TAGLINE = 'Your Ultimate Adult Entertainment Universe'
SITE_DESCRIPTION = (
    'goNuts - Stream premium adult content, explore diverse categories, '
    'and discover exclusive HD videos. The ultimate platform for adult entertainment '
    'with thousands of free videos updated daily.'
)
SITE_KEYWORDS = [
    'adult videos', 'premium adult content', 'HD porn', 'free adult videos',
    'streaming adult', 'adult entertainment', 'xxx videos', 'hentai',
    'adult categories', 'trending adult videos', 'goNuts'
]

# Social Media Links (update with actual links)
SOCIAL_LINKS = {
    'twitter': 'https://twitter.com/gonutsofficial',
    'instagram': 'https://instagram.com/gonutsofficial',
    'telegram': 'https://t.me/gonutsofficial',
    'discord': 'https://discord.gg/gonuts',
}

# SEO settings
SEO_DEFAULT_IMAGE = '/static/images/og-default.jpg'  # Default Open Graph image
SEO_TWITTER_HANDLE = '@gonutsofficial'
