from import_export import fields
from import_export.resources import ModelResource
from import_export.widgets import Widget

from df_survey.models import Question


class HashIdWidget(Widget):
    def render(self, value, obj=None):
        if value is None:
            return None
        return str(value)


class QuestionResource(ModelResource):
    id = fields.Field(column_name="id", attribute="id", widget=HashIdWidget())

    class Meta:
        model = Question
        fields = ["id", "question", "type", "format"]
        export_order = fields
