from typing import cast

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from training.models import Training

from .serializers import TrainingSerializer


class TrainingListAPIView(APIView):
    """Return trainings of an authenticated user."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """Return the authenticated user's trainings."""
        user = cast(User, request.user)
        trainings = (
            Training.objects.filter(user=user)
            .select_related('exercise')
            .order_by('-created_at', '-pk')
        )

        serializer = TrainingSerializer(instance=trainings, many=True)

        return Response(serializer.data)


class TrainingDetailAPIView(APIView):
    """Return one training owned by the authenticated user."""

    permission_classes = (IsAuthenticated,)

    def get(
        self,
        request: Request,
        training_id: int,
    ) -> Response:
        """Return one training owned by the authenticated user."""
        user = cast(User, request.user)
        training = get_object_or_404(
            Training.objects.select_related('exercise'),
            user=user,
            pk=training_id,
        )

        serializer = TrainingSerializer(instance=training)
        return Response(serializer.data)
