from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DfSurveyConfig(AppConfig):
    name = "df_survey"
    verbose_name = _("Django DF Survey")

    class DFMeta:
        api_path = "df_survey/"