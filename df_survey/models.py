# 1. There is no point prepending Survey to every model as this is the app name
# 2. Quite a few anti-patterns spotted

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models
from django.db.models import OuterRef, Subquery
from django.db.models.signals import m2m_changed, post_save
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


class SurveyQuestion(models.Model):
    survey = models.ForeignKey("Survey", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    sequence = models.PositiveSmallIntegerField(
        help_text="Display sequence, lower means first", default=1000
    )


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
    questions = models.ManyToManyField("Question", through=SurveyQuestion)

    def get_responses(self):
        qs = self.questions.all()
        users = (
            Response.objects.filter(survey__template=self)
            .values_list("survey__user__email", flat=True)
            .distinct()
        )

        for user in users:
            qs = qs.annotate(
                **{
                    user: Subquery(
                        queryset=Response.objects.filter(
                            question_id=OuterRef("pk"),
                            survey__template=self,
                            survey__user__email=user,
                        ).values_list("response")[:1]
                    )
                }
            )
        responses = [["Question", *users], list(qs.values_list("question", *users))]
        return responses

    def get_responses_matrix(self):
        questions = list(self.questions.all())
        responses = []
        # TODO: This seems like an anti pattern, what are you doing here?
        responses.append(["ID", "User", "Date", *[q.question for q in questions]])

        for survey in self.survey_set.prefetch_related("response_set").all():
            assert isinstance(survey, UserSurvey)
            survey_responses = {
                sr.question_id: sr.response for sr in survey.response_set.all()
            }
            responses.append(
                [
                    str(survey.id),
                    str(survey.user),
                    survey.created.isoformat(),
                    *[survey_responses.get(q.id, "") for q in questions],
                ]
            )
        return responses

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
        ...

    def __str__(self):
        return f"{self.user} - {self.survey}"

    class Meta:
        ordering = ["-modified"]


class Question(models.Model):
    class Type(models.TextChoices):
        text = "text", "Text"
        integer = "integer", "Integer"
        date = "date", "Date"
        single = "single", "Single choice"
        multi = "multi", "Multiple choice"

    question = models.CharField(max_length=255)
    type = models.CharField(choices=Type.choices, max_length=255)
    # TODO:
    # format should understand simple formats
    # min..max for numbers, e.g. 0..100
    # minLengh..maxLength for strings, e.g. 0..500
    # red|green|blue - choices
    format = models.TextField(default="", blank=True)

    def __str__(self):
        return self.question


class Response(models.Model):
    # TODO csv exporter
    usersurvey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField()


# TODO: I left this as pre_save because we cannot hande it in m2m_changed
# Because it fires for every m2m entry. So the method will be called many times
# that is not a problem because if instance.task is non null we will not touch it
@receiver(m2m_changed, sender=Survey)
def generate_task_from_questions(sender, instance, **kwargs):
    if not instance.task and instance.questions.exists():
        instance.task = SurveyKitRenderer.generate_task_from_survey(instance)
        instance.save(update_fields=["task"])


# TODO: This would make sense if we were doing rewrites
@receiver(post_save, sender=UserSurvey)
def parse_survey_response(sender, instance: UserSurvey, created, **kwargs):
    if instance.result and not instance.response_set.exists():
        questions = {q.id: q for q in instance.survey.questions.all()}
        for result in instance.pretty_results():
            if result.step_id in questions:
                Response.objects.create(
                    usersurvey=instance,
                    question=questions[result.step_id],
                    response=result.answer,
                )
