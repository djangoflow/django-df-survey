from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS = {
    "TEST_SETTING": "test",
}

api_settings = APISettings(getattr(settings, "DF_SURVEY", None), DEFAULTS)