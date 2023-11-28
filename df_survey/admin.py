from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import (
    AutocompleteSelectMultiple,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import JSONField, Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.timezone import now
from django_admin_relation_links import AdminChangeLinksMixin
from import_export import fields
from import_export.admin import ImportExportModelAdmin
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

User = get_user_model()


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


class SurveyUsersForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=AutocompleteSelectMultiple(
            UserSurvey._meta.get_field("user"),
            admin.site,
        ),
        required=False,
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=AutocompleteSelectMultiple(
            User._meta.get_field("groups"),
            admin.site,
        ),
        required=False,
    )

    def save(self, survey):
        users = self.cleaned_data["users"]
        groups = self.cleaned_data["groups"]

        created_user_surveys = []
        for user in User.objects.filter(
            Q(groups__in=groups) | Q(id__in=users.values("id"))
        ):
            user_survey, created = UserSurvey.objects.get_or_create(
                user=user, survey=survey
            )
            if created:
                created_user_surveys.append(user_survey)
        return created_user_surveys


class QuestionResource(ModelResource):
    instances_to_keep = set()
    id = fields.Field(column_name="id", attribute="id", widget=HashIdWidget())

    class Meta:
        model = Question
        fields = ["id", "question", "text", "type", "format"]
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
        instance.survey_id = kwargs["survey"].id
        instance.sequence = row_number

    def after_save_instance(self, instance, using_transactions, dry_run):
        self.instances_to_keep.add(instance.id)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        # TODO: uncomment if we want to remove questions that are not in the file
        # Question.objects.filter(survey_id=kwargs["survey_id"]).exclude(
        #     id__in=self.instances_to_keep
        # ).delete()
        pass


class QuestionResponseResource(ModelResource):
    class Meta:
        model = Question
        fields = ["question"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.survey = kwargs["survey"]
        self.fields.update(
            {
                user: fields.Field(column_name=user, attribute=user)
                for user in self.survey.get_respondents()
            }
        )


class QuestionResponseExport(ImportExportModelAdmin):
    model = Question
    export_template_name = "admin/df_survey/survey/export_question_responses.html"
    resource_class = QuestionResponseResource

    def get_export_queryset(self, request):
        return request.kwargs["survey"].get_responses()

    def get_export_resource_kwargs(self, request, *args, **kwargs):
        return {
            **super().get_export_resource_kwargs(request, *args, **kwargs),
            "survey": request.kwargs["survey"],
        }

    def get_export_filename(self, request, queryset, file_format):
        return "%s-%s-%s.%s" % (
            request.kwargs["survey"].title,
            "responses",
            now().strftime("%Y-%m-%d"),
            file_format.get_extension(),
        )


class QuestionImportExport(ImportExportModelAdmin):
    model = Question
    import_template_name = "admin/df_survey/survey/import_questions.html"
    export_template_name = "admin/df_survey/survey/export_questions.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_site = admin.site

    resource_class = QuestionResource

    def get_import_data_kwargs(self, request, *args, **kwargs):
        survey = request.kwargs["survey"]
        return {
            **super().get_import_data_kwargs(request, *args, **kwargs),
            "survey": survey,
            "question_ids": set(survey.question_set.all().values_list("id", flat=True)),
        }

    def get_export_queryset(self, request):
        return Question.objects.filter(survey__id=request.kwargs["survey"].id)

    def process_result(self, result, request):
        super().process_result(result, request)
        return HttpResponseRedirect(
            reverse(
                "admin:df_survey_survey_change",
                args=(request.kwargs["survey"].id,),
            )
        )

    def get_export_filename(self, request, queryset, file_format):
        return "%s-%s-%s.%s" % (
            request.kwargs["survey"].title,
            "questions",
            now().strftime("%Y-%m-%d"),
            file_format.get_extension(),
        )


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    search_fields = ("title",)

    list_display = (
        "id",
        "category",
        "title",
        "description",
        "users_total",
        "users_completed",
    )
    list_filter = ("category__slug",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate_stats()

    def users_total(self, obj):
        return obj.users_total

    users_total.admin_order_field = "users_total"

    def users_completed(self, obj):
        return obj.users_completed

    users_completed.admin_order_field = "users_completed"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<str:survey_id>/export_question_responses/",
                self.admin_site.admin_view(self.export_question_responses_view),
                name="df_survey_survey_export_question_responses",
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
            path(
                "<str:survey_id>/assign_users/",
                self.admin_site.admin_view(self.assign_users_view),
                name="df_survey_survey_assign_users",
            ),
        ]
        return custom_urls + urls

    def assign_users_view(self, request, **kwargs):
        self.set_request_kwargs(request, **kwargs)

        if request.method == "POST":
            form = SurveyUsersForm(request.POST)
            if form.is_valid():
                user_surveys = form.save(survey=request.kwargs["survey"])
                if len(user_surveys) > 0:
                    messages.success(
                        request,
                        "Successfully assigned %s users to the survey"
                        % len(user_surveys),
                    )
                else:
                    messages.warning(request, "No users were assigned to the survey")

                return redirect("admin:df_survey_survey_change", kwargs["survey_id"])
        else:
            form = SurveyUsersForm()

        context = {
            "form": form,
            "opts": self.model._meta,
            "survey": Survey.objects.get(id=kwargs["survey_id"]),
        }
        context.update(self.admin_site.each_context(request))
        return render(request, "admin/df_survey/survey/assign_users.html", context)

    def set_request_kwargs(self, request, **kwargs):
        request.kwargs = {"survey": Survey.objects.get(id=kwargs["survey_id"])}

    def import_questions_view(self, request, **kwargs):
        # Redirect to the generic import view with a context tailored for the specific survey
        self.set_request_kwargs(request, **kwargs)
        return QuestionImportExport(Survey, admin.site).import_action(request)

    def process_import_questions_view(self, request, **kwargs):
        # Redirect to the generic import view with a context tailored for the specific survey
        self.set_request_kwargs(request, **kwargs)
        return QuestionImportExport(Survey, admin.site).process_import(request)

    def export_question_responses_view(self, request, **kwargs):
        # Redirect to the generic export view with a context tailored for the specific survey
        self.set_request_kwargs(request, **kwargs)
        return QuestionResponseExport(Survey, admin.site).export_action(request)

    def export_questions_view(self, request, **kwargs):
        # Redirect to the generic export view with a context tailored for the specific survey
        self.set_request_kwargs(request, **kwargs)
        return QuestionImportExport(Survey, admin.site).export_action(request)

    # # TODO: (eugapx) This has to be implemented via importexport
    # def download_results(self, request, survey_template_id):
    #     # Logic to generate and return XLSX file
    #     response = HttpResponse(content_type="application/vnd.ms-excel")
    #     response[
    #         "Content-Disposition"
    #     ] = f'attachment; filename="survey_results_{survey_template_id}.xlsx"'
    #     survey = get_object_or_404(Survey, id=survey_template_id)
    #     wb = openpyxl.Workbook()
    #     ws = wb.active
    #     ws.title = "Survey Results"
    #     for row in survey.get_responses():
    #         ws.append(row)
    #
    #     wb.save(response)
    #     return response

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


class SurveyFilter(AutocompleteFilter):
    title = "Survey"
    field_name = "survey"


@admin.register(UserSurvey)
class UserSurveyAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    inlines = [ResponseInline]
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    autocomplete_fields = ["user", "survey"]
    list_display = (
        "id",
        "survey_link",
        "user",
        "created",
        "modified",
    )
    change_links = ["survey"]
    list_filter = (
        SurveyFilter,
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
