""" 
Django settings for packagebuilder project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    ENVIRONMENT=(str, 'production'),
    DEBUG=(bool, False),
    REDIS_URL=(str, 'redis://default:yBFAxLCCOvuobiLvdbSiVZLsKBUaVJoZ@redis.railway.internal:6379'),
    SALESFORCE_CONSUMER_KEY=(str, ''),
    SALESFORCE_CONSUMER_SECRET=(str, ''),
    SALESFORCE_API_VERSION=(int, 65),
    SALESFORCE_REDIRECT_URI=(str, ''),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

ENVIRONMENT = env('ENVIRONMENT')
IS_LOCAL = ENVIRONMENT == 'dev'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if IS_LOCAL else bool(env('DEBUG'))
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG


ADMINS = (
    ('Ben Edwards', 'ben@edwards.nz'),
)

if not IS_LOCAL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    CSRF_TRUSTED_ORIGINS = [
        'https://web-production-9e9fa.up.railway.app',
        'https://packagebuilder.cloudtoolkit.co'
    ]

ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'buildpackage',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'packagebuilder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'packagebuilder.wsgi.application'

MAX_CONN_AGE = 600

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# For running on server
if not IS_LOCAL:
    # Configure Django for DATABASE_URL environment variable.
    DATABASES["default"] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ["PGDATABASE"],
        'USER': os.environ["PGUSER"],
        'PASSWORD': os.environ["PGPASSWORD"],
        'HOST': os.environ["PGHOST"],
        'PORT': os.environ["PGPORT"],
    }

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env('REDIS_URL'),
            "OPTIONS": {
                "ssl_cert_reqs": None
            }
        }
    }

    
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage"
    },
    # Enable WhiteNoise's GZip and Brotli compression of static assets:
    # https://whitenoise.readthedocs.io/en/latest/django.html#add-compression-and-caching-support
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Don't store the original (un-hashed filename) version of static files, to reduce slug size:
# https://whitenoise.readthedocs.io/en/latest/django.html#WHITENOISE_KEEP_ONLY_HASHED_FILES
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

# Celery settings
CELERY_BROKER_URL = env('REDIS_URL')
BROKER_POOL_LIMIT = 1

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-nz'
TIME_ZONE = 'Pacific/Auckland'
USE_I18N = True
USE_L10N = True
USE_TZ = True


STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

SALESFORCE_CONSUMER_KEY = env('SALESFORCE_CONSUMER_KEY')
SALESFORCE_CONSUMER_SECRET = env('SALESFORCE_CONSUMER_SECRET')
SALESFORCE_REDIRECT_URI = env('SALESFORCE_REDIRECT_URI')
SALESFORCE_API_VERSION = int(env('SALESFORCE_API_VERSION'))

SALESFORCE_REST_URL = '/services/data/v%d.0/' % SALESFORCE_API_VERSION

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

