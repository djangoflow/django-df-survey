from django.contrib import admin
from django.db.models import JSONField
from django_admin_relation_links import AdminChangeLinksMixin
from jsoneditor.forms import JSONEditor

from .models import (
    SurveyCategory,
    SurveyTemplate,
    UserSurvey,
)


@admin.register(SurveyCategory)
class SurveyCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "slug")


@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
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
