from rest_framework import viewsets, generics, permissions

from df_survey.drf.serializers import UserSurveyStepSerializer, UserSurveySerializer
from df_survey.models import UserSurveyStep, UserSurvey


class UserSurveyViewSet(viewsets.GenericViewSet, generics.mixins.ListModelMixin,generics.mixins.RetrieveModelMixin, generics.mixins.UpdateModelMixin):
    queryset = UserSurvey.objects.all()
    serializer_class = UserSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class UserSurveyStepViewSet(viewsets.GenericViewSet, generics.mixins.UpdateModelMixin, generics.mixins.RetrieveModelMixin):
    queryset = UserSurveyStep.objects.all()
    serializer_class = UserSurveyStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user_survey__user=self.request.user)
