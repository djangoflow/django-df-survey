from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from ..models import Survey
from .serializers import SurveyDetailsSerializer, SurveySerializer


class SurveyViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = SurveyDetailsSerializer
    queryset = Survey.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return SurveySerializer
        return self.serializer_class
