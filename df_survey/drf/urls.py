from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .viewsets import UserSurveyStepViewSet, UserSurveyViewSet

urlpatterns = []

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("user-surveys", UserSurveyViewSet, basename="user-surveys")
router.register(
    "user-survey-steps", UserSurveyStepViewSet, basename="user-survey-steps"
)

urlpatterns += router.urls
