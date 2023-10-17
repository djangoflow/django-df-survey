from typing import Any

from django.conf import settings
from django.db import models


class Step(models.Model):
    class Type(models.TextChoices):
        information = "information"
        text = "text"
        integer = "integer"
        single_select = "single_select"
        multi_select = "multi_select"
        date = "date"
        time = "time"
        datetime = "datetime"

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, default="", blank=True)
    description = models.TextField(default="", blank=True)
    image = models.ImageField(upload_to="survey/steps", null=True, blank=True)
    type = models.CharField(max_length=255, choices=Type.choices)
    # TODO: define jsonschema based on type
    validators = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.title} <{self.type}>"


# class InformationStep(models.Model):
#     step = models.OneToOneField(Step, on_delete=models.CASCADE)
#     icon =
#     avatar =
#     image =
#     description =
#
# class TextStep(models.Model):
#     pass
#
# class IntegerStep(models.Model):
#     ...
#
# class SingleSelectStep(models.Model):
#     """
#     Multiple options
#     """
#     step = models.OneToOneField(Step, on_delete=models.CASCADE)
#
# class MultiSelectStep(models.Model):
#     """
#     Multiple options
#     """
#     step = models.OneToOneField(Step, on_delete=models.CASCADE)
#
#
# class SelectOption(models.Model):
#     select = models.ForeignKey(Select)
#     is_default = models.BooleanField()
#
#
# class DateTimeStep(models.Model):
#     ...
#
# class StepCondition(models.Model):
#     source = models.ForeignKey(Step, on_delete=models.CASCADE)
#     condition = models.CharField(max_length=256)


class Survey(models.Model):
    # is_template = models.BooleanField(default=False)
    title = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)

    steps = models.ManyToManyField(Step, through="SurveyStep")

    def __str__(self) -> str:
        return self.title


class SurveyStep(models.Model):
    sequence = models.PositiveIntegerField(default=1000)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("survey", "step"),
            ("survey", "sequence"),
        )
        ordering = ("sequence",)

    def __str__(self) -> str:
        return f"{self.survey} - {self.step}"


class UserSurvey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    current_step = models.ForeignKey(
        Step, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.user} - {self.survey}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            for step in self.survey.steps.all():
                UserSurveyStep.objects.create(step=step, user_survey=self)

    # class Event(models.TextChoices):
    #     STARTED = "started"
    #     ABORTED = "aborted"
    #     PAUSED = "paused"
    #     COMPLETED = "completed"
    #
    # events = ModelEvents(choices=Event.choices)


# class UserSurveyEvent(models.Model):
#     at = models.DateTimeField(auto_now_add=True)
#     event = models.CharField(max_length=10, choices=UserSurvey.Event.choices)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     user_survey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)


class UserSurveyStep(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE)
    user_survey = models.ForeignKey(
        UserSurvey, on_delete=models.CASCADE, related_name="steps"
    )
    response = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user_survey} - {self.step}"
