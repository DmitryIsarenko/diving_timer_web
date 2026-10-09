from http import HTTPStatus
from typing import cast

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from training.models import Exercise, FourStepBreathingExercise, Training

from .serializers import (
    FourStepBreathingTrainingCreateSerializer,
    FourStepBreathingTrainingSerializer,
    TrainingActionSerializer,
    TrainingSerializer,
)


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

        return Response(serializer.data, status=HTTPStatus.OK)


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

        return Response(serializer.data, status=HTTPStatus.OK)

    def delete(
        self,
        request: Request,
        training_id: int,
    ) -> Response:
        """Deletion."""
        user = cast(User, request.user)
        training = get_object_or_404(
            Training.objects.select_related('exercise'),
            user=user,
            pk=training_id,
        )

        if training.status in {
            Training.Status.CANCELLED,
            Training.Status.COMPLETED,
        }:
            training.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response(status=HTTPStatus.BAD_REQUEST)

    def patch(
        self,
        request: Request,
        training_id: int,
    ) -> Response:
        """Change state by action."""
        user = cast(User, request.user)
        training = get_object_or_404(
            Training.objects.select_related('exercise'),
            user=user,
            pk=training_id,
        )
        change_serializer = TrainingActionSerializer(data=request.data)
        change_serializer.is_valid(raise_exception=True)

        if change_serializer.validated_data['action'] == 'pause':
            if training.status != Training.Status.IN_PROGRESS:
                return Response(status=HTTPStatus.CONFLICT)
            training.status = Training.Status.PAUSED
            if training.first_paused_at is None:
                training.first_paused_at = timezone.now()
            training.save(update_fields=['status', 'first_paused_at'])
        elif change_serializer.validated_data['action'] == 'resume':
            if training.status != Training.Status.PAUSED:
                return Response(status=HTTPStatus.CONFLICT)
            training.status = Training.Status.IN_PROGRESS
            training.save(update_fields=['status'])
        elif change_serializer.validated_data['action'] == 'complete':
            if training.status != Training.Status.IN_PROGRESS:
                return Response(status=HTTPStatus.CONFLICT)
            training.status = Training.Status.COMPLETED
            training.completed_at = timezone.now()
            training.save(update_fields=['status', 'completed_at'])

        elif change_serializer.validated_data['action'] == 'cancel':
            if training.status not in (
                Training.Status.IN_PROGRESS,
                Training.Status.PAUSED,
                Training.Status.NOT_STARTED,
            ):
                return Response(status=HTTPStatus.CONFLICT)
            training.status = Training.Status.CANCELLED
            training.cancelled_at = timezone.now()
            training.save(update_fields=['status', 'cancelled_at'])
        else:
            return Response(status=HTTPStatus.CONFLICT)

        response_serializer = TrainingSerializer(instance=training)
        return Response(response_serializer.data, status=HTTPStatus.OK)


class FourStepBreathingTrainingDetailAPIView(APIView):
    """Return one four-step breathing training of the current user."""

    permission_classes = (IsAuthenticated,)

    def get(
        self,
        request: Request,
        training_id: int,
    ) -> Response:
        """Return one owned four-step breathing training."""
        user = cast(User, request.user)

        training = get_object_or_404(
            Training.objects.select_related(
                'exercise',
                'exercise__fourstepbreathingexercise',
            ),
            user=user,
            pk=training_id,
            exercise__exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
        )
        response_serializer = FourStepBreathingTrainingSerializer(
            instance=training
        )
        return Response(response_serializer.data, status=HTTPStatus.OK)


class FourStepBreathingTrainingCreateAPIView(APIView):
    """Creation view for 4-step exercise."""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        """POST create 4-step training of a user."""
        user = cast(User, request.user)
        create_serializer = FourStepBreathingTrainingCreateSerializer(
            data=request.data
        )
        create_serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            exercise = FourStepBreathingExercise.objects.create(
                exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
                **create_serializer.validated_data,
            )
            training = Training.objects.create(
                user=user,
                exercise=exercise,
                status=Training.Status.IN_PROGRESS,
            )
        response_serializer = FourStepBreathingTrainingSerializer(
            instance=training
        )
        return Response(response_serializer.data, status=HTTPStatus.CREATED)


class FourStepBreathingTrainingListAPIView(APIView):
    """List all 4-step trainings."""

    permission_classes = (IsAuthenticated,)

    def get(
        self,
        request: Request,
    ) -> Response:
        """GET all 4-step trainings of a user."""
        user = cast(User, request.user)
        trainings = (
            Training.objects.filter(
                user=user,
                exercise__exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
            )
            .select_related('exercise', 'exercise__fourstepbreathingexercise')
            .order_by('-created_at', '-pk')
        )
        response_serializer = FourStepBreathingTrainingSerializer(
            instance=trainings,
            many=True,
        )
        return Response(response_serializer.data, status=HTTPStatus.OK)
