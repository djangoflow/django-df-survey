from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS = {}

api_settings = APISettings(getattr(settings, "DF_SURVEY", None), DEFAULTS)
