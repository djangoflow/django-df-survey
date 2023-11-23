# 1. There is no point prepending Survey to every model as this is the app name
# 2. Quite a few anti-patterns spotted

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from df_notifications.decorators import (
    register_reminder_model,
    register_rule_model,
)
from df_notifications.models import (
    NotificationModelAsyncReminder,
    NotificationModelAsyncRule,
)
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models
from django.db.models import OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils.models import TimeStampedModel

from df_survey.renderers import SurveyKitRenderer

if TYPE_CHECKING:
    from django.contrib.auth.models import User
else:
    User = get_user_model()


class Category(models.Model):
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


class Survey(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    sequence = models.PositiveSmallIntegerField(
        help_text="Display sequence, lower means first", default=1000
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    task = models.JSONField(validators=[validate_task_json], null=True, blank=True)

    def generate_task(self):
        self.task = SurveyKitRenderer.generate_task_from_survey(self)

    def get_response_users(self):
        return (
            Response.objects.filter(usersurvey__survey=self)
            .values_list("usersurvey__user__email", flat=True)
            .exclude(usersurvey__user__email="")
            .exclude(usersurvey__user__email__isnull=True)
            .distinct()
        )

    def get_responses(self):
        qs = self.question_set.all()

        for user in self.get_response_users():
            qs = qs.annotate(
                **{
                    user: Coalesce(
                        Subquery(
                            queryset=Response.objects.filter(
                                question_id=OuterRef("pk"),
                                usersurvey__survey=self,
                                usersurvey__user__email=user,
                            ).values_list("response")[:1]
                        ),
                        Value("", output_field=models.TextField()),
                    )
                }
            )

        return qs
        # responses = [["Question", *users], *(qs.values_list("question", *users))]
        # return responses

    def __str__(self):
        return f"{self.id}: {self.title}"


class UserSurveyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("survey__category")

    def create_for_users(self, survey=None, users=None):
        if survey:
            users = users or User.objects.filter(is_active=True).exclude(
                id__in=self.filter(survey=survey).values("user_id")
            )
            for user in users:
                self.get_or_create(user=user, survey=survey)


class UserSurvey(TimeStampedModel):
    user_attribute = "user"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
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
                q["stepIdentifier"]["id"]: q["title"] for q in self.survey.task["steps"]
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
        questions = {q.id: q for q in self.survey.questions.all()}
        for result in self.pretty_results():
            if result.step_id in questions:
                Response.objects.create(
                    usersurvey=self,
                    question=questions[result.step_id],
                    response=result.answer,
                )

    def __str__(self):
        return f"{self.user} - {self.survey}"

    class Meta:
        ordering = ["-modified"]
        unique_together = ["user", "survey"]


class Question(models.Model):
    class Type(models.TextChoices):
        text = "text", "Text"
        integer = "integer", "Integer"
        date = "date", "Date"
        single = "single", "Single choice"
        multi = "multi", "Multiple choice"

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    sequence = models.PositiveSmallIntegerField(
        help_text="Display sequence, lower means first", default=1000
    )
    question = models.CharField(max_length=255)
    type = models.CharField(choices=Type.choices, max_length=255)
    format = models.TextField(default="", blank=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ["sequence"]


class Response(models.Model):
    # TODO csv exporter
    usersurvey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField()


@register_rule_model
class UserSurveyNotification(NotificationModelAsyncRule):
    model = UserSurvey
    tracking_fields = []


@register_reminder_model
class UserSurveysReminder(NotificationModelAsyncReminder):
    model = UserSurvey

    def get_model_queryset(self) -> QuerySet[UserSurvey]:
        return super().get_model_queryset().filter(result__isnull=True)

    def get_users(self, instance: UserSurvey) -> list:
        return [instance.user]


# TODO: This would make sense if we were doing rewrites
@receiver(post_save, sender=UserSurvey)
def parse_survey_response(sender, instance: UserSurvey, created, **kwargs):
    if instance.result and not instance.response_set.exists():
        instance.parse_survey_response()
