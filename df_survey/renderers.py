from typing import Optional

from .models import Survey, UserSurvey


class BaseSurveyRenderer:
    def render_survey(self, survey: Survey, usersurvey: Optional[UserSurvey]) -> any:
        pass


class JSONSurveyRenderer(BaseSurveyRenderer):
    def render_survey(self, survey: Survey, usersurvey: Optional[UserSurvey]) -> dict:
        pass
    def render_responses(self, survey: Survey, usersurvey: Optional[UserSurvey]) -> dict:
        pass


class SurveyKitJSONRenderer(JSONSurveyRenderer):
    """
    https://pub.dev/packages/survey_kit
    """
    pass


class SurveyFlowJSONRenderer(JSONSurveyRenderer):
    """
    https://pub.dev/packages/survey_flow
    """
    pass
