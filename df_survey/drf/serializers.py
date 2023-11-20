import json

from django.template import Context, Template
from drf_spectacular.utils import extend_schema_field
from hashid_field.rest import HashidSerializerCharField
from rest_framework import serializers

from ..models import UserSurvey


class UserSurveySerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True)
    title = serializers.CharField(source="survey.title", read_only=True)
    description = serializers.CharField(source="survey.description", read_only=True)
    category = serializers.CharField(source="survey.category.slug", read_only=True)
    completed = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        attrs = super().to_representation(instance)
        if instance.result:
            attrs["completed"] = instance.modified
        return attrs

    class Meta:
        model = UserSurvey
        read_only_fields = ("created", "modified")
        fields = read_only_fields + (
            "id",
            "title",
            "category",
            "description",
            "completed",
        )


class UserSurveyDetailsSerializer(UserSurveySerializer):
    task = serializers.SerializerMethodField("get_task")
    result = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs["user"] = self.context["request"].user
        return attrs

    class Meta(UserSurveySerializer.Meta):
        fields = (*UserSurveySerializer.Meta.fields, "task", "result")

    @extend_schema_field(serializers.JSONField)
    def get_task(self, obj: UserSurvey):
        template = Template(json.dumps(obj.survey.task))
        task_str = template.render(Context({"user": obj.user}))
        task = json.loads(task_str)

        results = {res.step_id: res for res in obj.pretty_results()}

        for step in task["steps"]:
            result = results.get(step["stepIdentifier"]["id"])
            if not result:
                continue

            if "answerFormat" not in step:
                step["answerFormat"] = {}

            step["answerFormat"]["defaultValue"] = result.answer_full
            step["answerFormat"]["defaultSelection"] = result.answer_full

        return task
