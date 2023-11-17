from django.contrib import admin
from django.db.models import JSONField
from django_admin_relation_links import AdminChangeLinksMixin
from import_export.admin import ImportExportMixin
from jsoneditor.forms import JSONEditor

from .models import (
    SurveyCategory,
    SurveyQuestion,
    SurveyTemplate,
    SurveyTemplateQuestion,
    UserSurvey,
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

    list_display = ("id", "category", "title", "description")
    list_filter = ("category__slug",)

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
    list_display = ("question", "type", "validators")
    search_fields = ("question",)
    list_filter = ("type",)
