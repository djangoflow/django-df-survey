from django.db.models import QuerySet
from rest_framework import generics, permissions, viewsets

from df_survey.drf.serializers import (
    UserSurveySerializer,
    UserSurveyStepSerializer,
)
from df_survey.models import UserSurvey, UserSurveyStep


class UserSurveyViewSet(
    viewsets.GenericViewSet,
    generics.mixins.ListModelMixin,
    generics.mixins.RetrieveModelMixin,
    generics.mixins.UpdateModelMixin,
):
    queryset = UserSurvey.objects.all()
    serializer_class = UserSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserSurvey]:
        return super().get_queryset().filter(user=self.request.user)


class UserSurveyStepViewSet(
    viewsets.GenericViewSet,
    generics.mixins.UpdateModelMixin,
    generics.mixins.RetrieveModelMixin,
):
    queryset = UserSurveyStep.objects.all()
    serializer_class = UserSurveyStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserSurveyStep]:
        return super().get_queryset().filter(user_survey__user=self.request.user)
