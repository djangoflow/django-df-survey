from typing import Any

from django.http import HttpRequest
from rest_framework import permissions, views
from rest_framework.response import Response


class TestView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        return Response({"message": "test"})
