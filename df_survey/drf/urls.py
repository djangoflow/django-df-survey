from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .viewsets import SurveyViewSet

urlpatterns = []

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("user-surveys", SurveyViewSet, basename="user-surveys")

urlpatterns += router.urls
