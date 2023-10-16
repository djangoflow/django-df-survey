from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Step(models.Model):
    validators = models.JSONField()
    title =
    subtitle =


class InformationStep(models.Model):
    step = models.OneToOneField(Step, on_delete=models.CASCADE)
    icon =
    avatar =
    image =
    description =

class TextStep():
    
class IntegerStep():

class SingleSelectStep(models.Model):
    """
    Multiple options
    """
    step = models.OneToOneField(Step, on_delete=models.CASCADE)

class MultiSelectStep(models.Model):
    """
    Multiple options
    """
    step = models.OneToOneField(Step, on_delete=models.CASCADE)


class SelectOption(models.Model):
    select = models.ForeignKey(Select)
    is_default = models.BooleanField()


class DateTimeStep()

# class StepCondition(models.Model):
#     source = models.ForeignKey(Step, on_delete=models.CASCADE)
#     condition = models.CharField(max_length=256)


class Survey(models.Model):
    is_template = models.BooleanField(default=False)
    title =
    description =


class SurveyStep(models.Model):
    sequence = models.PositiveIntegerField(default=1000, unique=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.CASCADE)


class UserSurvey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    cursor = models.ForeignKey(SurveyStep, on_delete=models.SET_NULL, null=True, blank=True)

    class Event(models.TextChoices):
        STARTED = "started"
        ABORTED = "aborted"
        PAUSED = "paused"
        COMPLETED = "completed"
    #
    # events = ModelEvents(choices=Event.choices)

class UserSurveyEvent(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    event = models.CharField(max_length=10, choices=UserSurvey.Event.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usersurvey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)


class UserResponse(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE)
    usersurvey = models.ForeignKey(UserSurvey, on_delete=models.CASCADE)
    response = models.JSONField()
