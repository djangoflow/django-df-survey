from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from model_utils.models import TimeStampedModel

if TYPE_CHECKING:
    from django.contrib.auth.models import User
else:
    User = get_user_model()


class SurveyCategory(models.Model):
    slug = models.CharField(max_length=128)

    def __str__(self):
        return self.slug

    class Meta:
        verbose_name_plural = "Survey categories"


def validate_task_json(json):
    # 1. Ensure all target steps are present in rules
    step_identifiers = [step["stepIdentifier"]["id"] for step in json["steps"]]

    errors = []
    if "rules" in json:
        line = 0
        for rule in json["rules"]:
            if rule["type"] == "conditional":
                step_id = rule["triggerStepIdentifier"]["id"]
                if step_id not in step_identifiers:
                    print("VVVs")

                    errors.append(
                        {
                            "task": f"Invalid triggerStepIdentifier '{step_id}' in rule '{line}'"
                        }
                    )
                for k, v in rule["values"].items():
                    if v not in step_identifiers:
                        errors.append(
                            {
                                "task": [
                                    f"Invalid target step '{v}' in value '{k}' of rule '{line}'"
                                ]
                            }
                        )
            line += 1
        if errors:
            raise exceptions.ValidationError(errors)


class SurveyTemplateQuestion(models.Model):
    surveytemplate = models.ForeignKey("SurveyTemplate", on_delete=models.CASCADE)
    surveyquestion = models.ForeignKey("SurveyQuestion", on_delete=models.CASCADE)
    sequence = models.PositiveSmallIntegerField(
        help_text="Display sequence, lower means first", default=1000
    )


class SurveyTemplate(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    sequence = models.PositiveSmallIntegerField(
        help_text="Display sequence, lower means first", default=1000
    )
    category = models.ForeignKey(
        SurveyCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    task = models.JSONField(validators=[validate_task_json], null=True, blank=True)
    questions = models.ManyToManyField("SurveyQuestion", through=SurveyTemplateQuestion)

    def generate_task_from_questions(self):  # noqa: C901
        steps = []
        for question in self.questions.all():
            if question.type == "text":
                fmt = {
                    "type": "text",
                }
            elif question.type == "integer":
                fmt = {
                    "type": "integer",
                }
                if question.validators.get("max", False):
                    fmt["maximumValue"] = question.validators["max"]
                if question.validators.get("min", False):
                    fmt["minimumValue"] = question.validators["min"]
            elif question.type == "date":
                fmt = {
                    "type": "date",
                }
                if question.validators.get("max", False):
                    fmt["maxDate"] = question.validators["max"]
                if question.validators.get("min", False):
                    fmt["minDate"] = question.validators["min"]
            elif question.type == "options":
                choices = question.validators.get("options", [])
                selection_limit = question.validators.get("max", 1)
                if selection_limit == 1:
                    fmt = {
                        "type": "single",
                        "otherField": False,
                        "choices": choices,
                    }
                else:
                    fmt = {
                        "type": "multiple",
                        "otherField": False,
                        "choices": choices,
                        "selectionLimit": selection_limit,
                    }

            else:
                raise exceptions.ValidationError(
                    f"Invalid question type '{question.type}'"
                )
            steps.append(
                {
                    "type": "question",
                    "title": question.question,
                    "answerFormat": fmt,
                    "stepIdentifier": {"id": slugify(question.question)},
                }
            )

        return {
            "id": slugify(self.title),
            "type": "navigable",
            "rules": [],
            "steps": steps,
        }


class UserSurveyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("template", "template__category")

    def create_for_users(self, template=None, users=None):
        if template:
            users = users or User.objects.filter(is_active=True).exclude(
                id__in=self.filter(template=template).values("user_id")
            )
            for user in users:
                self.get_or_create(user=user, template=template)


class UserSurvey(TimeStampedModel):
    user_attribute = "user"
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    template = models.ForeignKey(SurveyTemplate, on_delete=models.CASCADE)
    result = models.JSONField(null=True, blank=True)
    objects = UserSurveyManager()

    def pretty_results(self):
        @dataclass
        class ResultEntry:
            step_id: str
            question: str
            answer: str
            answer_full: Any

        results = []
        if self.result:
            questions = {
                q["stepIdentifier"]["id"]: q["title"]
                for q in self.template.task["steps"]
            }

            for result in self.result["results"]:
                try:
                    res = result["results"][0]["result"]
                    answer_full = res
                    if isinstance(res, list) and len(res) == 1:
                        res = res[0]

                    if (
                        isinstance(res, dict)
                        and len(res) == 2
                        and "text" in res
                        and "value" in res
                        and res["text"] == res["value"]
                    ):
                        res = res["value"]

                    step_id = result["id"]["id"]
                    if step_id in questions:
                        results.append(
                            ResultEntry(
                                step_id=step_id,
                                question=questions[step_id],
                                answer=res,
                                answer_full=answer_full,
                            )
                        )
                except LookupError:
                    pass
        return results

    def save(self, *args, **kwargs):
        if self.result is not None:
            self.to_digest = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.template}"

    class Meta:
        ordering = ["-modified"]


class SurveyQuestion(models.Model):
    class Type(models.TextChoices):
        text = "text", "Text"
        integer = "integer", "Integer"
        date = "date", "Date"
        options = "options", "Options"

    question = models.CharField(unique=True, max_length=255)
    type = models.CharField(choices=Type.choices, max_length=255)
    validators = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.question


class UserSurveyResponse(models.Model):
    # TODO csv exporter
    survey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    response = models.TextField()


@receiver(pre_save, sender=SurveyTemplate)
def generate_task_from_questions(sender, instance, **kwargs):
    if not instance.task:
        instance.generate_task_from_questions()
