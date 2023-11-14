from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .viewsets import UserSurveyViewSet

urlpatterns = []

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("user_surveys", UserSurveyViewSet, basename="user_surveys")

urlpatterns += router.urls
