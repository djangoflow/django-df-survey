# Generated by Django 4.2.5 on 2023-11-18 06:26

import df_survey.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import hashid_field.field
import model_utils.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("slug", models.CharField(max_length=128)),
            ],
            options={
                "verbose_name_plural": "Survey categories",
            },
        ),
        migrations.CreateModel(
            name="Question",
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
                            ("single", "Single choice"),
                            ("multi", "Multiple choice"),
                        ],
                        max_length=255,
                    ),
                ),
                ("format", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="Template",
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
                ("title", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "sequence",
                    models.PositiveSmallIntegerField(
                        default=1000, help_text="Display sequence, lower means first"
                    ),
                ),
                (
                    "task",
                    models.JSONField(
                        blank=True,
                        null=True,
                        validators=[df_survey.models.validate_task_json],
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="df_survey.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TemplateQuestion",
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
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.question",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.template",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="template",
            name="questions",
            field=models.ManyToManyField(
                through="df_survey.TemplateQuestion", to="df_survey.question"
            ),
        ),
        migrations.CreateModel(
            name="Survey",
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
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("result", models.JSONField(blank=True, null=True)),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="df_survey.template",
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
            options={
                "ordering": ["-modified"],
            },
        ),
        migrations.CreateModel(
            name="Response",
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
                        to="df_survey.question",
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
        ),
    ]
