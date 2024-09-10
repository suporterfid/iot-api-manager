from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class SmartreaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.smartreader"
    verbose_name = _("smartreader_app_verbose_name")
