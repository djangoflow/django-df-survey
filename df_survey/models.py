from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models
from django.db.models.signals import post_save, pre_save
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
                if question.format.get("max", False):
                    fmt["maximumValue"] = question.format["max"]
                if question.format.get("min", False):
                    fmt["minimumValue"] = question.format["min"]
            elif question.type == "date":
                fmt = {
                    "type": "date",
                }
                if question.format.get("max", False):
                    fmt["maxDate"] = question.format["max"]
                if question.format.get("min", False):
                    fmt["minDate"] = question.format["min"]
            elif question.type == "singlechoice":
                fmt = {
                    "type": "single",
                    "otherField": False,
                    "choices": question.format.get("options", []),
                }
            elif question.type == "multichoice":
                fmt = {
                    "type": "multiple",
                    "otherField": False,
                    "choices": question.format.get("options", []),
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
                    "stepIdentifier": {"id": question.slug},
                }
            )

        self.task = {
            "id": slugify(self.title),
            "type": "navigable",
            "rules": [],
            "steps": steps,
        }

    def responses_matrix(self):
        questions = list(self.questions.all())
        responses = []
        responses.append(["ID", "User", "Date", *[q.question for q in questions]])

        for user_survey in self.usersurvey_set.prefetch_related(
            "usersurveyresponse_set"
        ).all():
            assert isinstance(user_survey, UserSurvey)
            survey_responses = {
                sr.question_id: sr.response
                for sr in user_survey.usersurveyresponse_set.all()
            }
            responses.append(
                [
                    str(user_survey.id),
                    str(user_survey.user),
                    user_survey.created.isoformat(),
                    *[survey_responses.get(q.id, "") for q in questions],
                ]
            )
        return responses


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

                    if isinstance(res, list) and all(
                        isinstance(r, dict) and r.get("text") and r.get("value")
                        for r in res
                    ):
                        res = ", ".join([r["value"] for r in res])

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

    def parse_survey_response(self):
        ...

    def __str__(self):
        return f"{self.user} - {self.template}"

    class Meta:
        ordering = ["-modified"]


class SurveyQuestion(models.Model):
    class Type(models.TextChoices):
        text = "text", "Text"
        integer = "integer", "Integer"
        date = "date", "Date"
        singlechoice = "singlechoice", "Choice"
        multichoice = "multichoice", "Multichoice"

    question = models.CharField(unique=True, max_length=255)
    type = models.CharField(choices=Type.choices, max_length=255)
    format = models.JSONField(default=dict, blank=True)

    @property
    def slug(self):
        return slugify(self.question)

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


@receiver(post_save, sender=UserSurvey)
def parse_survey_response(sender, instance: UserSurvey, created, **kwargs):
    if instance.result and not instance.usersurveyresponse_set.exists():
        questions = {q.slug: q for q in instance.template.questions.all()}
        for result in instance.pretty_results():
            if result.step_id in questions:
                UserSurveyResponse.objects.create(
                    survey=instance,
                    question=questions[result.step_id],
                    response=result.answer,
                )
