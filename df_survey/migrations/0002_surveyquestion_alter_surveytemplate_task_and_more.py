# Generated by Django 4.2.6 on 2023-11-17 14:47

import df_survey.models
from django.db import migrations, models
import django.db.models.deletion
import hashid_field.field


class Migration(migrations.Migration):
    dependencies = [
        ("df_survey", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SurveyQuestion",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question", models.CharField(max_length=255, unique=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("integer", "Integer"),
                            ("date", "Date"),
                            ("singlechoice", "Choice"),
                            ("multichoice", "Multichoice"),
                        ],
                        max_length=255,
                    ),
                ),
                ("format", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.AlterField(
            model_name="surveytemplate",
            name="task",
            field=models.JSONField(
                blank=True, null=True, validators=[df_survey.models.validate_task_json]
            ),
        ),
        migrations.CreateModel(
            name="UserSurveyResponse",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("response", models.TextField()),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.surveyquestion",
                    ),
                ),
                (
                    "survey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.usersurvey",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SurveyTemplateQuestion",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sequence",
                    models.PositiveSmallIntegerField(
                        default=1000, help_text="Display sequence, lower means first"
                    ),
                ),
                (
                    "surveyquestion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.surveyquestion",
                    ),
                ),
                (
                    "surveytemplate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.surveytemplate",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="surveytemplate",
            name="questions",
            field=models.ManyToManyField(
                through="df_survey.SurveyTemplateQuestion",
                to="df_survey.surveyquestion",
            ),
        ),
    ]
