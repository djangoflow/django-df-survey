import openpyxl
import tablib
from django import forms
from django.contrib import admin
from django.db.models import JSONField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django_admin_relation_links import AdminChangeLinksMixin
from import_export.admin import ImportExportMixin
from jsoneditor.forms import JSONEditor

from .models import (
    Category,
    Question,
    Response,
    Survey,
    SurveyQuestion,
    UserSurvey,
)
from .resources import QuestionResource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "slug")


class SurveyQuestionAdmin(admin.TabularInline):
    model = SurveyQuestion
    extra = 3


class SurveyAdminForm(forms.ModelForm):
    questions_file = forms.FileField(required=False)

    class Meta:
        model = Survey
        fields = "__all__"

    def save(self, commit=True):
        survey = super().save(commit)
        survey_file = self.cleaned_data.get("questions_file")
        if survey_file:
            dataset = tablib.Dataset()
            dataset.load(survey_file.read())
            question_resource = QuestionResource()
            rows = question_resource.import_data(dataset, dry_run=False)
            for idx, row in enumerate(rows):
                SurveyQuestion.objects.create(
                    survey=survey, question_id=row.object_id, sequence=idx + 1
                )
            survey.generate_task()
            survey.save()

        return survey


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    form = SurveyAdminForm
    inlines = [SurveyQuestionAdmin]
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    list_display = ("id", "category", "title", "description", "download")
    list_filter = ("category__slug",)

    def download(self, obj):
        return format_html(
            '<a href="{}" download>Download</a>',
            reverse("admin:template_download", args=[obj.id]),
        )

    download.short_description = "Download Results"

    # TODO: (eugapx) This has to be implemented via importexport
    def download_results(self, request, survey_template_id):
        # Logic to generate and return XLSX file
        response = HttpResponse(content_type="application/vnd.ms-excel")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="survey_results_{survey_template_id}.xlsx"'
        survey = get_object_or_404(Survey, id=survey_template_id)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Survey Results"
        for row in survey.get_responses():
            ws.append(row)

        wb.save(response)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "download/<str:survey_template_id>/",
                self.admin_site.admin_view(self.download_results),
                name="template_download",
            ),
        ]
        return custom_urls + urls

    @admin.action(description="Assign this survey to all users")
    def create_for_all_users(self, request, queryset):
        for survey in queryset:
            UserSurvey.objects.create_for_users(survey=survey, users=None)

    def generate_tasks(self, request, queryset):
        for survey in queryset:
            survey.generate_task()
            survey.save()

    actions = [create_for_all_users, generate_tasks]


@admin.register(UserSurvey)
class UserSurveyAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    list_display = (
        "id",
        "survey_link",
        "user",
        "created",
        "modified",
    )
    change_links = ["survey"]
    list_filter = (
        "survey__category__slug",
        ("result", admin.EmptyFieldListFilter),
    )
    search_fields = ("user__email", "survey__title")

    def parse_survey_response(self, request, queryset):
        for user_survey in queryset:
            user_survey.parse_survey_response()

    actions = [parse_survey_response]


@admin.register(Question)
class QuestionAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = QuestionResource
    list_display = ("question", "type", "format")
    search_fields = ("question",)
    list_filter = ("type",)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("usersurvey", "question", "response")
    autocomplete_fields = ("usersurvey", "question")
