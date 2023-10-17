from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS = {
    "USER_ADMIN_SEARCH_FIELDS": ["email", "first_name", "last_name"],
}

api_settings = APISettings(getattr(settings, "DF_SURVEY", None), DEFAULTS)
