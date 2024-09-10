import os
from pathlib import Path
from pythonjsonlogger import jsonlogger
from kombu import Exchange, Queue
from celery.schedules import crontab
from datetime import datetime
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "web"

SECRET_KEY = "django-insecure-8gw&=e(wa%vxaye11h7mg2v1oaxee5ykw5kxh=a-urt$6j*0i)"

SITE_NAME = _("Reader Manager")

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

DEBUG = True
ALLOWED_HOSTS = ["*"]

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1000
SESSION_SAVE_EVERY_REQUEST = True


# region: MQTT Settings
MQTT_BROKER_URL = os.environ.get("MQTT_BROKER_URL", "localhost")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883))
MQTT_KEEPALIVE_INTERVAL = int(os.environ.get("MQTT_KEEPALIVE_INTERVAL", 60))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
MQTT_USE_TLS = bool(int(os.environ.get("MQTT_USE_TLS", "0")))
MQTT_TLS_CA_CERTS = os.environ.get("MQTT_TLS_CA_CERTS", "")
# endregion

# region: DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": "db",
        "PORT": "5432",
    }
}
# endregion

# region: LOGS
LOG_DIR = DATA_DIR / "log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE_PATH = os.path.join(LOG_DIR, f'django_{datetime.now().strftime("%Y%m%d")}.log')
LOG_LOGSTASH_DB = os.path.join(LOG_DIR, "logstash.db")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "logstash": {
            "class": "logstash_async.handler.AsynchronousLogstashHandler",
            "host": "logstash",  # Refers to the Logstash service in Docker Compose
            "port": 5044,
            "database_path": LOG_LOGSTASH_DB,
            "ssl_enable": False,
            "ssl_verify": False,
            "formatter": "json",
        },
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_FILE_PATH,
            "formatter": "verbose",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console", "logstash"],
            "level": "INFO",
            "propagate": True,
        },
        "config": {
            "handlers": ["console", "logstash"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
# endregion

# region CELERY
CELERY_BEAT_SCHEDULE = {
    "update-departure-time-every-minute": {
        "task": "config.tasks.process_departure_time",
        "schedule": crontab(minute="*"),  # Run every minute
    },
}

CELERY_BROKER_URL = "amqp://user:password@rabbitmq:5672//"
CELERY_RESULT_BACKEND = "rpc://"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

CELERY_TASK_QUEUES = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("webhook_queue", Exchange("webhook_exchange"), routing_key="webhook.#"),
    Queue(
        "webhook_settings_queue",
        Exchange("webhook_settings_exchange"),
        routing_key="webhook_settings.#",
    ),
    Queue(
        "mqtt_settings_queue",
        Exchange("mqtt_settings_exchange"),
        routing_key="mqtt_settings.#",
    ),
)

CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_EXCHANGE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"

# Routing configuration
CELERY_TASK_ROUTES = {
    "config.tasks.process_webhook": {
        "queue": "webhook_queue",
        "routing_key": "webhook.process",
        "exchange": "webhook",
    },
    "config.tasks.process_webhook_settings": {
        "queue": "webhook_settings_queue",
        "routing_key": "webhook_settings.process",
        "exchange": "webhook_settings",
    },
    "config.tasks.process_mqtt_settings": {
        "queue": "mqtt_settings_queue",
        "routing_key": "mqtt_settings.process",
        "exchange": "mqtt_settings",
    },
}
# endregion

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "crispy_forms",
    "crispy_bootstrap5",
    "apps.readers",
    "apps.smartreader"
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

CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# region: Internationalization
LANGUAGE_CODE = "pt-br"
LANGUAGES = (
    ("en-us", _("English")),
    ("pt-br", _("Portuguese")),
)
LOCALE_PATHS = [
    BASE_DIR / "locale",
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True
# endregion

STATIC_URL = "/static/"
STATIC_ROOT = DATA_DIR / "static"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

CSRF_TRUSTED_ORIGINS = [
    "https://localhost",
    "http://localhost",
]