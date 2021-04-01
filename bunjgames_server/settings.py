import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
SECRET_KEY = os.environ.get('BUNJGAMES_SECRET_KEY', '*w')
DEBUG = os.environ.get('BUNJGAMES_DEBUG', 'False').lower() != 'false'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'common',
    'whirligig',
    'jeopardy',
    'weakest',
    'feud',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'bunjgames_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'bunjgames_server.wsgi.application'
ASGI_APPLICATION = "bunjgames_server.routing.application"

CORS_ORIGIN_ALLOW_ALL = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('BUNJGAMES_DATABASE_NAME', 'bunjgames'),
        'USER': os.environ.get('BUNJGAMES_DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('BUNJGAMES_DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('BUNJGAMES_DATABASE_HOST', '127.0.0.1'),
        'PORT': int(os.environ.get('BUNJGAMES_DATABASE_PORT', '5432')),
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'server.log'),
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_ROOT_WHIRLIGIG = os.path.join(BASE_DIR, 'media', 'whirligig')
MEDIA_ROOT_JEOPARDY = os.path.join(BASE_DIR, 'media', 'jeopardy')
MEDIA_ROOT_WEAKEST = os.path.join(BASE_DIR, 'media', 'weakest')
MEDIA_ROOT_FEUD = os.path.join(BASE_DIR, 'media', 'feud')
MEDIA_URL = '/media/'

JEOPARDY_IS_POST_EVENT_REQUIRED = False
