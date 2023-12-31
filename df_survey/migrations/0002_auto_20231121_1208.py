# Generated by Django 4.2.6 on 2023-11-21 12:08
from datetime import timedelta

from django.db import migrations


def init_data(apps, schema_editor):
    UserSurveyNotification = apps.get_model("df_survey", "UserSurveyNotification")
    UserSurveyNotification.objects.create(
        channel="push",
        template_prefix="df_notifications/usersurveynotification/",
    )
    UserSurveyNotification.objects.create(
        channel="email",
        template_prefix="df_notifications/usersurveynotification/",
    )
    UserSurveysReminder = apps.get_model("df_survey", "UserSurveysReminder")
    UserSurveysReminder.objects.create(
        channel="push",
        template_prefix="df_notifications/usersurveysreminder/",
        delay=timedelta(hours=1),
    )
    UserSurveysReminder.objects.create(
        channel="email",
        template_prefix="df_notifications/usersurveysreminder/",
        delay=timedelta(days=1),
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("df_survey", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(init_data, noop),
    ]
