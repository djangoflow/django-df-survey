from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from ..models import UserSurvey
from .serializers import UserSurveyDetailsSerializer, UserSurveySerializer


class UserSurveyViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = UserSurveyDetailsSerializer
    queryset = UserSurvey.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user,
            survey__task__isnull=False,
        )

    def get_serializer_class(self):
        if self.action == "list":
            return UserSurveySerializer
        return self.serializer_class
