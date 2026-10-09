from http import HTTPStatus
from typing import cast

from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from accounts.models import User
from training.models import Exercise, FourStepBreathingExercise, Training


class TestTrainingListAPIView:
    """Tests for the general trainings list API."""

    def test_anonymous_user_cannot_get_trainings(
        self,
        api_client: APIClient,
    ) -> None:
        """Anonymous user receives an authentication error."""
        response = api_client.get(reverse('training_api_v1:trainings'))

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_user_gets_only_own_trainings(
        self,
        user_api_client: APIClient,
        default_training: Training,
        other_user: User,
    ) -> None:
        """List excludes another user's trainings."""
        other_exercise = FourStepBreathingExercise.objects.create(
            exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
        )
        other_training = Training.objects.create(
            user=other_user,
            exercise=other_exercise,
        )

        response = user_api_client.get(reverse('training_api_v1:trainings'))

        assert response.status_code == HTTPStatus.OK
        assert [item['id'] for item in response.data] == [default_training.pk]
        assert other_training.pk not in [item['id'] for item in response.data]


class TestTrainingDetailAPIView:
    """Tests for the general training detail API."""

    def test_owner_gets_training(
        self,
        user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Owner receives general training data."""
        response = user_api_client.get(
            reverse(
                'training_api_v1:training-detail',
                kwargs={'training_id': default_training.pk},
            )
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data['id'] == default_training.pk
        assert response.data['exercise_type'] == (
            Exercise.ExerciseType.FOUR_STEP_BREATHING
        )

    def test_other_user_gets_not_found(
        self,
        other_user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Another user cannot access a training."""
        response = other_user_api_client.get(
            reverse(
                'training_api_v1:training-detail',
                kwargs={'training_id': default_training.pk},
            )
        )

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestFourStepBreathingTrainingAPIView:
    """Tests for four-step breathing training endpoints."""

    def test_anonymous_user_cannot_create_training(
        self,
        api_client: APIClient,
        four_step_api_payload: dict[str, int],
    ) -> None:
        """Anonymous user cannot create a training."""
        response = api_client.post(
            reverse('training_api_v1:four-step-breathing-create'),
            data=four_step_api_payload,
            format='json',
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post_creates_exercise_and_training(
        self,
        user_api_client: APIClient,
        user: User,
        four_step_api_payload: dict[str, int],
    ) -> None:
        """Valid POST creates linked exercise and training."""
        response = user_api_client.post(
            reverse('training_api_v1:four-step-breathing-create'),
            data=four_step_api_payload,
            format='json',
        )

        training = Training.objects.get(pk=response.data['id'])
        exercise: FourStepBreathingExercise = cast(
            FourStepBreathingExercise,
            FourStepBreathingExercise.objects.get(
                pk=training.exercise.pk,
            ),
        )

        assert response.status_code == HTTPStatus.CREATED
        assert training.user == user
        assert training.status == Training.Status.IN_PROGRESS
        assert exercise.exercise_type == (
            Exercise.ExerciseType.FOUR_STEP_BREATHING
        )
        assert exercise.round_count == four_step_api_payload['round_count']
        assert (
            response.data['exercise']['round_count']
            == (four_step_api_payload['round_count'])
        )

    def test_post_with_invalid_data_creates_nothing(
        self,
        user_api_client: APIClient,
        four_step_api_payload: dict[str, int],
    ) -> None:
        """Invalid POST does not create related models."""
        trainings_count_before = Training.objects.count()
        exercises_count_before = FourStepBreathingExercise.objects.count()
        four_step_api_payload['round_count'] = 0

        response = user_api_client.post(
            reverse('training_api_v1:four-step-breathing-create'),
            data=four_step_api_payload,
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert Training.objects.count() == trainings_count_before
        assert FourStepBreathingExercise.objects.count() == (
            exercises_count_before
        )

    def test_list_returns_only_four_step_trainings(
        self,
        user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Four-step list returns the owner's four-step trainings."""
        response = user_api_client.get(
            reverse('training_api_v1:four-step-breathing')
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data[0]['id'] == default_training.pk
        assert response.data[0]['exercise_type'] == (
            Exercise.ExerciseType.FOUR_STEP_BREATHING
        )
        assert response.data[0]['exercise']['round_count'] == 5

    def test_detail_returns_training_and_exercise_settings(
        self,
        user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Four-step detail returns training and nested settings."""
        response = user_api_client.get(
            reverse(
                'training_api_v1:four-step-breathing-detail',
                kwargs={'training_id': default_training.pk},
            )
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data['id'] == default_training.pk
        assert response.data['exercise']['id'] == (
            default_training.exercise.pk
        )

        assert response.data['exercise']['inhale_duration_seconds'] == 5

    def test_other_user_cannot_get_four_step_detail(
        self,
        other_user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Another user cannot access four-step training details."""
        response = other_user_api_client.get(
            reverse(
                'training_api_v1:four-step-breathing-detail',
                kwargs={'training_id': default_training.pk},
            )
        )

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestTrainingActionAPIView:
    """Tests for training state transitions."""

    @pytest.mark.parametrize(
        ('action', 'expected_status', 'timestamp_field'),
        (
            ('pause', Training.Status.PAUSED, 'first_paused_at'),
            ('complete', Training.Status.COMPLETED, 'completed_at'),
            ('cancel', Training.Status.CANCELLED, 'cancelled_at'),
        ),
    )
    def test_allowed_actions_change_training(
        self,
        user_api_client: APIClient,
        default_training: Training,
        action: str,
        expected_status: str,
        timestamp_field: str,
    ) -> None:
        """Allowed actions update the training state."""
        default_training.status = Training.Status.IN_PROGRESS
        default_training.save(update_fields=['status'])

        response = user_api_client.patch(
            reverse(
                'training_api_v1:training-detail',
                kwargs={'training_id': default_training.pk},
            ),
            data={'action': action},
            format='json',
        )
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.OK
        assert default_training.status == expected_status
        assert getattr(default_training, timestamp_field) is not None

    def test_invalid_action_returns_bad_request(
        self,
        user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Unknown action returns validation errors."""
        response = user_api_client.patch(
            reverse(
                'training_api_v1:training-detail',
                kwargs={'training_id': default_training.pk},
            ),
            data={'action': 'unknown'},
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_invalid_transition_returns_conflict(
        self,
        user_api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Completed training cannot be paused."""
        default_training.status = Training.Status.COMPLETED
        default_training.save(update_fields=['status'])

        response = user_api_client.patch(
            reverse(
                'training_api_v1:training-detail',
                kwargs={'training_id': default_training.pk},
            ),
            data={'action': 'pause'},
            format='json',
        )
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.CONFLICT
        assert default_training.status == Training.Status.COMPLETED
