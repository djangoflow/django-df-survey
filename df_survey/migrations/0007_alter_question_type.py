# Generated by Django 4.2.6 on 2023-11-28 08:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("df_survey", "0006_question_text_alter_question_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="type",
            field=models.CharField(
                choices=[
                    ("info", "Info"),
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