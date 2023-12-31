# Generated by Django 4.2.6 on 2023-11-27 14:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("df_survey", "0005_alter_response_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="text",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="question",
            name="type",
            field=models.CharField(
                choices=[
                    ("intro", "Intro"),
                    ("completion", "Completion"),
                    ("text", "Text"),
                    ("integer", "Integer"),
                    ("date", "Date"),
                    ("single", "Single choice"),
                    ("multi", "Multiple choice"),
                ],
                max_length=255,
            ),
        ),
    ]
