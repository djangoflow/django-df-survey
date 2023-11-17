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


class ValidatorsWidget(Widget):
    def render(self, value, obj=None):
        return json.dumps(value)

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None

        if value.startswith("{"):
            return json.loads(value)

        result = {}
        for part in value.split(";"):
            key, val = part.split(":")
            if "," in val:
                val = [v.strip() for v in val.split(",")]
            else:
                val = val.strip()
            result[key.strip()] = val
        return result


class SurveyQuestionResource(ModelResource):
    id = fields.Field(column_name="id", attribute="id", widget=HashIdWidget())
    validators = fields.Field(
        column_name="validators", attribute="validators", widget=ValidatorsWidget()
    )

    class Meta:
        model = SurveyQuestion
        fields = ["id", "question", "type", "validators"]
        export_order = fields
