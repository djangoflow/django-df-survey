# Generated by Django 4.2.6 on 2023-10-17 10:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import hashid_field.field


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Step",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.CharField(blank=True, default="", max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="survey/steps"),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("information", "Information"),
                            ("text", "Text"),
                            ("integer", "Integer"),
                            ("single_select", "Single Select"),
                            ("multi_select", "Multi Select"),
                            ("date", "Date"),
                            ("time", "Time"),
                            ("datetime", "Datetime"),
                        ],
                        max_length=255,
                    ),
                ),
                ("validators", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="Survey",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
            ],
        ),
        migrations.CreateModel(
            name="UserSurvey",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "current_step",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="df_survey.step",
                    ),
                ),
                (
                    "survey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.survey",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserSurveyStep",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("response", models.JSONField(blank=True, null=True)),
                (
                    "step",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="df_survey.step"
                    ),
                ),
                (
                    "user_survey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="df_survey.usersurvey",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SurveyStep",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sequence", models.PositiveIntegerField(default=1000)),
                (
                    "step",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="df_survey.step"
                    ),
                ),
                (
                    "survey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.survey",
                    ),
                ),
            ],
            options={
                "ordering": ("sequence",),
                "unique_together": {("survey", "step"), ("survey", "sequence")},
            },
        ),
        migrations.AddField(
            model_name="survey",
            name="steps",
            field=models.ManyToManyField(
                through="df_survey.SurveyStep", to="df_survey.step"
            ),
        ),
    ]
