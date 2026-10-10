import os
from pathlib import Path

from dotenv import load_dotenv

from diving_timer.logging_config import building_logging_config


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

SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY or not SECRET_KEY.strip():
    raise ValueError('SECRET_KEY must not be empty!')

DEBUG = parse_bool(os.getenv('DEBUG'))

LOGGING = building_logging_config(
    base_dir=BASE_DIR,
    debug=DEBUG,
)

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
    # DRF
    'rest_framework',
    # project apps
    'accounts.apps.AccountsConfig',
    'training.apps.TrainingConfig',
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


LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# === Email / Gmail SMTP ===
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
EMAIL_TIMEOUT = 10

# === Email verification ===
EMAIL_VERIFICATION_MAX_AGE = 60 * 60 * 24
SITE_BASE_URL = os.getenv(
    'SITE_BASE_URL',
    'http://127.0.0.1:8000',
).rstrip('/')
