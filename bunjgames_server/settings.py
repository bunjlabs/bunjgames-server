import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('BUNJGAMES_SECRET_KEY', '*')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('BUNJGAMES_DEBUG', 'False').lower() != 'false'

ALLOWED_HOSTS = ['*']

# Application definition

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
    'clubchat',
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

CHANNEL_REDIS_HOST = os.environ.get('BUNJGAMES_REDIS_HOST', '127.0.0.1')
CHANNEL_REDIS_PORT = os.environ.get('BUNJGAMES_REDIS_PORT', '6379')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(CHANNEL_REDIS_HOST, int(CHANNEL_REDIS_PORT))],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': BASE_DIR / 'db.sqlite3',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('BUNJGAMES_DATABASE_NAME', 'bunjgames'),
        'USER': os.environ.get('BUNJGAMES_DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('BUNJGAMES_DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('BUNJGAMES_DATABASE_HOST', '127.0.0.1'),
        'PORT': int(os.environ.get('BUNJGAMES_DATABASE_PORT', '5432')),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_ROOT_WHIRLIGIG = os.path.join(BASE_DIR, 'media', 'whirligig')
MEDIA_ROOT_JEOPARDY = os.path.join(BASE_DIR, 'media', 'jeopardy')
MEDIA_URL = '/media/'

JEOPARDY_IS_POST_EVENT_REQUIRED = False

CLUBCHAT_TELEGRAM_BOT_API_KEY = os.environ.get('CLUBCHAT_TELEGRAM_BOT_API_KEY', '')
CLUBCHAT_TELEGRAM_BOT_TOKEN = os.environ.get('CLUBCHAT_TELEGRAM_BOT_TOKEN', '')
