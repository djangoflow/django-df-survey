from rest_framework import mixins
from rest_framework.exceptions import ValidationError
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

    def perform_update(self, serializer):
        if serializer.instance.result:
            raise ValidationError("Your submission has already been recorded.")
        return super().perform_update(serializer)

    def get_object(self):
        pk = self.kwargs.get("pk", "")
        if pk.startswith("@"):
            survey_pk = pk[1:]
            return UserSurvey.objects.get_or_create(
                user=self.request.user,
                survey_id=survey_pk,
            )[0]
        return super().get_object()
