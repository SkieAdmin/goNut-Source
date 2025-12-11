"""
Django settings for core project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-6c49h$%0zbghaapjzoqd5fehy7n1#+vgnv)t*8t&tveeduc_9t'

DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://gonut.click',
    'https://www.gonut.click',
]

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

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
