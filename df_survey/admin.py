import openpyxl
from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import JSONField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django_admin_relation_links import AdminChangeLinksMixin
from import_export import fields
from import_export.admin import ImportExportModelAdmin
from import_export.instance_loaders import ModelInstanceLoader
from import_export.resources import ModelResource
from jsoneditor.forms import JSONEditor

from .models import (
    Category,
    Question,
    Response,
    Survey,
    UserSurvey,
    UserSurveyNotification,
)
from .resources import HashIdWidget


class ReadOnlyInline(admin.TabularInline):
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "slug")


class QuestionInline(admin.TabularInline):
    formfield_overrides = {models.TextField: {"widget": forms.TextInput()}}
    model = Question
    extra = 0

    # fields = ("question", "type", "format", "order")


class SurveyAdminForm(forms.ModelForm):
    questions_file = forms.FileField(required=False)

    class Meta:
        model = Survey
        fields = "__all__"

    # def save(self, commit=True):
    #     survey = super().save(commit)
    #     survey_file = self.cleaned_data.get("questions_file")
    #     if survey_file:
    #         dataset = tablib.Dataset()
    #         dataset.load(survey_file.read())
    #         question_resource = QuestionResource()
    #         rows = question_resource.import_data(dataset, dry_run=False)
    #         for idx, row in enumerate(rows):
    #             SurveyQuestion.objects.create(
    #                 survey=survey, question_id=row.object_id, sequence=idx + 1
    #             )
    #         survey.generate_task()
    #         survey.save()
    #
    #     return survey


class QuestionInstanceLoader(ModelInstanceLoader):
    def get_queryset(self):
        ...


class QuestionResource(ModelResource):
    instances_to_keep = set()
    id = fields.Field(column_name="id", attribute="id", widget=HashIdWidget())

    class Meta:
        model = Question
        fields = ["id", "question", "type", "format"]
        export_order = fields

    def before_import_row(self, row, row_number=None, **kwargs):
        # Clean IDs if we are importing questions from another survey
        if row["id"] not in kwargs["question_ids"]:
            row["id"] = None
        if row["question"] is None:
            row["question"] = ""

    def skip_row(self, instance, original, row, import_validation_errors=None):
        return not instance.question

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        instance.survey_id = kwargs["survey_id"]
        instance.sequence = row_number

    def after_save_instance(self, instance, using_transactions, dry_run):
        self.instances_to_keep.add(instance.id)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        Question.objects.filter(survey_id=kwargs["survey_id"]).exclude(
            id__in=self.instances_to_keep
        ).delete()


class QuestionImportExport(ImportExportModelAdmin):
    model = Question
    import_template_name = "admin/df_survey/survey/import_questions.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_site = admin.site

    resource_class = QuestionResource

    def get_import_data_kwargs(self, request, *args, **kwargs):
        survey_id = request.kwargs["survey_id"]
        return {
            **super().get_import_data_kwargs(request, *args, **kwargs),
            "survey_id": survey_id,
            "question_ids": set(
                Question.objects.filter(survey_id=survey_id).values_list(
                    "id", flat=True
                )
            ),
        }

    def get_export_queryset(self, request):
        return Question.objects.filter(survey__id=request.kwargs["survey_id"])

    def process_result(self, result, request):
        super().process_result(result, request)
        return HttpResponseRedirect(
            reverse(
                "admin:df_survey_survey_change",
                args=(request.kwargs["survey_id"],),
            )
        )


@admin.register(Survey)
class SurveyAdmin(ImportExportModelAdmin):
    form = SurveyAdminForm
    inlines = [QuestionInline]
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    list_display = ("id", "category", "title", "description", "download")
    list_filter = ("category__slug",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "download/<str:survey_template_id>/",
                self.admin_site.admin_view(self.download_results),
                name="template_download",
            ),
            path(
                "<str:survey_id>/import_questions/",
                self.admin_site.admin_view(self.import_questions_view),
                name="df_survey_survey_import_questions",
            ),
            path(
                "<str:survey_id>/process_import_questions/",
                self.admin_site.admin_view(self.process_import_questions_view),
                name="df_survey_survey_process_import_questions",
            ),
            path(
                "<str:survey_id>/export_questions/",
                self.admin_site.admin_view(self.export_questions_view),
                name="df_survey_survey_export_questions",
            ),
        ]
        return custom_urls + urls

    def import_questions_view(self, request, **kwargs):
        # Redirect to the generic import view with a context tailored for the specific survey
        request.kwargs = kwargs
        return QuestionImportExport(Survey, admin.site).import_action(request)

    def process_import_questions_view(self, request, **kwargs):
        # Redirect to the generic import view with a context tailored for the specific survey
        request.kwargs = kwargs
        return QuestionImportExport(Survey, admin.site).process_import(request)

    def export_questions_view(self, request, **kwargs):
        # Redirect to the generic export view with a context tailored for the specific survey
        request.kwargs = kwargs
        return QuestionImportExport(Survey, admin.site).export_action(request)

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

    @admin.action(description="Assign this survey to all users")
    def create_for_all_users(self, request, queryset):
        for survey in queryset:
            UserSurvey.objects.create_for_users(survey=survey, users=None)

    def generate_tasks(self, request, queryset):
        for survey in queryset:
            survey.generate_task()
            survey.save()

    actions = [create_for_all_users, generate_tasks]

    class Media:
        css = {"all": ("df_survey/admin/css/surveys.css",)}


class ResponseInline(ReadOnlyInline):
    model = Response
    extra = 0


@admin.register(UserSurvey)
class UserSurveyAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    inlines = [ResponseInline]
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

    def send_notifications(self, request, queryset):
        for user_survey in queryset:
            for notification in UserSurveyNotification.objects.all():
                notification.send(user_survey)

    actions = [parse_survey_response, send_notifications]

    class Media:
        css = {"all": ("df_survey/admin/css/user_surveys.css",)}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "type", "format")
    search_fields = ("question",)
    list_filter = ("type",)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("usersurvey", "question", "response")
    autocomplete_fields = ("usersurvey", "question")
