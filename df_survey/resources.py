import json

from import_export import fields
from import_export.resources import ModelResource
from import_export.widgets import Widget

from df_survey.models import SurveyQuestion


class HashIdWidget(Widget):
    def render(self, value, obj=None):
        if value is None:
            return None
        return str(value)


class SurveyQuestionFormatWidget(Widget):
    def render(self, value, obj=None):
        return json.dumps(value)

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None

        if value.startswith("{"):
            return json.loads(value)

        result = {}
        if ".." in value:
            mn, mx = value.split("..")
            result.update(
                {
                    "min": mn.strip(),
                    "max": mx.strip(),
                }
            )
        elif ";" in value:
            result["options"] = [v.strip() for v in value.split(";")]

        return result


class SurveyQuestionResource(ModelResource):
    id = fields.Field(column_name="id", attribute="id", widget=HashIdWidget())
    format = fields.Field(
        column_name="format", attribute="format", widget=SurveyQuestionFormatWidget()
    )

    class Meta:
        model = SurveyQuestion
        fields = ["id", "question", "type", "format"]
        export_order = fields
