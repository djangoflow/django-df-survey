from typing import Any, Sequence

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.http import HttpRequest

from df_survey.models import (
    Step,
    Survey,
    SurveyStep,
    UserSurvey,
    UserSurveyStep,
)
from df_survey.settings import api_settings

"""



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
    subtitle = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='survey/steps')
    type = models.CharField(max_length=255, choices=Type.choices)
    validators = models.JSONField()




class Survey(models.Model):
    # is_template = models.BooleanField(default=False)
    title = models.CharField(max_length=255)
    description = models.TextField()

    steps = models.ManyToManyField(Step, through='SurveyStep')


class SurveyStep(models.Model):
    sequence = models.PositiveIntegerField(default=1000)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('survey', 'sequence'),
            ('survey', 'step'),
        )
        ordering = ('sequence',)


class UserSurvey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    current_step = models.ForeignKey(SurveyStep, on_delete=models.SET_NULL, null=True, blank=True)

class UserSurveyStep(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE)
    survey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)
    response = models.JSONField()

"""


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    search_fields = ("title", "subtitle")
    list_display = ("title", "subtitle", "type")


class SurveyStepInline(admin.TabularInline):
    model = SurveyStep
    extra = 0
    autocomplete_fields = ("step",)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    list_display = ("title", "step_count")
    inlines = (SurveyStepInline,)

    def step_count(self, obj: Survey) -> int:
        return obj.steps.count()


class UserSurveyStepInline(admin.TabularInline):
    model = UserSurveyStep
    extra = 0
    autocomplete_fields = ("step",)


@admin.register(UserSurvey)
class UserSurveyAdmin(admin.ModelAdmin):
    def get_search_fields(self, request: HttpRequest) -> Sequence[str]:
        return (
            *(f"user__{f}" for f in api_settings.USER_ADMIN_SEARCH_FIELDS),
            "survey__title",
        )

    list_display = ("user", "survey", "current_step")
    autocomplete_fields = ("user", "current_step")
    inlines = (UserSurveyStepInline,)

    def get_inlines(
        self, request: HttpRequest, obj: Any
    ) -> list[type[InlineModelAdmin]]:
        if obj is None:
            return []
        return super().get_inlines(request, obj)
