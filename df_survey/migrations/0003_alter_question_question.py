# Generated by Django 4.2.6 on 2023-11-20 12:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("df_survey", "0002_alter_question_format"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="question",
            field=models.CharField(max_length=255),
        ),
    ]