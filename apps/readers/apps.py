from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReadersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.readers"
    verbose_name = _("readers")
