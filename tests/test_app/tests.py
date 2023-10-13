from django.conf import settings
from rest_framework.test import APIClient

from df_survey.settings import api_settings


def test_test_endpoint_returns_200(client: APIClient) -> None:
    response = client.get("/api/v1/df_module/test/")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_settings_rewrite() -> None:

    assert api_settings.TEST_SETTING == settings.DF_SURVEY['TEST_SETTING']