import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv


load_dotenv()


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse a boolean variable from environmental variable."""
    if not value:
        return default

    normalized_value = value.lower().strip()

    if normalized_value in ('1', 'yes', 'y', 'true', 'on'):
        return True
    if normalized_value in ('0', 'no', 'n', 'false', 'off'):
        return False

    raise ValueError(f'Invalid boolean value {value!r}')


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', get_random_secret_key())

DEBUG = parse_bool(os.getenv('DEBUG'))

raw_hosts: str = os.getenv('DJANGO_ALLOWED_HOSTS') or 'localhost, 127.0.0.1'
ALLOWED_HOSTS = [host for host in raw_hosts.split(sep=',') if host.strip()]


LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'


INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # project apps
    'accounts.apps.AccountsConfig',
    'timer.apps.TimerConfig',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'diving_timer.urls'

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

WSGI_APPLICATION = 'diving_timer.wsgi.application'
ASGI_APPLICATION = 'diving_timer.asgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    },
    'testdb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'testdb.sqlite3',
    },
}


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


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
