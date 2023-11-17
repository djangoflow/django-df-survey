import openpyxl
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
    SurveyCategory,
    SurveyQuestion,
    SurveyTemplate,
    SurveyTemplateQuestion,
    UserSurvey,
    UserSurveyResponse,
)
from .resources import SurveyQuestionResource


@admin.register(SurveyCategory)
class SurveyCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "slug")


class SurveyTemplateQuestionAdmin(admin.TabularInline):
    model = SurveyTemplateQuestion
    extra = 3


@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
    inlines = [SurveyTemplateQuestionAdmin]
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    list_display = ("id", "category", "title", "description", "download")
    list_filter = ("category__slug",)

    def download(self, obj):
        return format_html(
            '<a href="{}" download>Download</a>',
            reverse("admin:surveytemplate_download", args=[obj.id]),
        )

    download.short_description = "Download Results"

    def download_results(self, request, survey_template_id):
        # Logic to generate and return XLSX file
        response = HttpResponse(content_type="application/vnd.ms-excel")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="survey_results_{survey_template_id}.xlsx"'
        survey = get_object_or_404(SurveyTemplate, id=survey_template_id)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Survey Results"
        for row in survey.responses_matrix():
            ws.append(row)

        wb.save(response)
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "download/<str:survey_template_id>/",
                self.admin_site.admin_view(self.download_results),
                name="surveytemplate_download",
            ),
        ]
        return custom_urls + urls

    @admin.action(description="Assign this survey to all users")
    def create_for_all_users(self, request, queryset):
        for template in queryset:
            UserSurvey.objects.create_for_users(template=template, users=None)

    actions = [create_for_all_users]


@admin.register(UserSurvey)
class UserSurveyAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    list_display = (
        "id",
        "template_link",
        "user",
        "created",
        "modified",
    )
    change_links = ["template"]
    list_filter = (
        "template__category__slug",
        ("result", admin.EmptyFieldListFilter),
    )
    search_fields = ("user__email", "template__title")


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = SurveyQuestionResource
    list_display = ("question", "type", "format")
    search_fields = ("question",)
    list_filter = ("type",)


@admin.register(UserSurveyResponse)
class UserSurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "question", "response")
    autocomplete_fields = ("survey", "question")
