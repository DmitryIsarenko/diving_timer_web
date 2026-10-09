from http import HTTPStatus

from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from training.models import FourStepBreathingExercise, Training


class TestTrainingListAPIView:
    """Tests for the training list API endpoint."""

    def test_anonymous_user_cannot_get_trainings(
        self,
        api_client: APIClient,
    ) -> None:
        """Anonymous users cannot get the training list."""
        url = reverse('training_api_v1:training-list')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_user_gets_empty_list_without_trainings(
        self,
        api_client: APIClient,
        user: User,
    ) -> None:
        """An authenticated user without trainings gets an empty list."""
        api_client.force_authenticate(user=user)
        url = reverse('training_api_v1:training-list')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    def test_user_gets_only_own_trainings(
        self,
        api_client: APIClient,
        user: User,
        other_user: User,
        default_4_step_exercise: FourStepBreathingExercise,
        default_training: Training,
    ) -> None:
        """The endpoint returns only the current user's trainings."""
        other_training = Training.objects.create(
            user=other_user,
            exercise=default_4_step_exercise,
        )
        api_client.force_authenticate(user=user)
        url = reverse('training_api_v1:training-list')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.OK

        returned_ids = {
            training_data['id'] for training_data in response.json()
        }

        assert default_training.pk in returned_ids
        assert other_training.pk not in returned_ids

    def test_trainings_are_ordered_from_newest_to_oldest(
        self,
        api_client: APIClient,
        user: User,
        default_4_step_exercise: FourStepBreathingExercise,
        default_training: Training,
    ) -> None:
        """The newest training is returned first."""
        newest_training = Training.objects.create(
            user=user,
            exercise=default_4_step_exercise,
        )
        api_client.force_authenticate(user=user)
        url = reverse('training_api_v1:training-list')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.OK

        returned_ids = [
            training_data['id'] for training_data in response.json()
        ]

        assert returned_ids == [
            newest_training.pk,
            default_training.pk,
        ]

    def test_response_has_expected_fields_and_values(
        self,
        api_client: APIClient,
        user: User,
        default_training: Training,
    ) -> None:
        """The response contains the public training representation."""
        api_client.force_authenticate(user=user)
        url = reverse('training_api_v1:training-list')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.OK

        training_data = response.json()[0]

        assert set(training_data) == {
            'id',
            'status',
            'exercise_type',
            'first_paused_at',
            'cancelled_at',
            'created_at',
            'completed_at',
        }
        assert training_data['id'] == default_training.pk
        assert training_data['status'] == Training.Status.NOT_STARTED
        assert training_data['exercise_type'] == 'four_step_breathing'
        assert training_data['created_at'] is not None
        assert training_data['first_paused_at'] is None
        assert training_data['cancelled_at'] is None
        assert training_data['completed_at'] is None

    def test_post_is_not_allowed(
        self,
        api_client: APIClient,
        user: User,
    ) -> None:
        """The read-only list endpoint does not accept POST."""
        api_client.force_authenticate(user=user)
        url = reverse('training_api_v1:training-list')

        response = api_client.post(url, data={}, format='json')

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestTrainingDetailAPIView:
    """Tests for the training detail API endpoint."""

    def test_anonymous_user_cannot_get_training(
        self,
        api_client: APIClient,
        default_training: Training,
    ) -> None:
        """Anonymous users cannot get training details."""
        url = reverse(
            'training_api_v1:training-detail',
            kwargs={'training_id': default_training.pk},
        )

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_owner_gets_training(
        self,
        api_client: APIClient,
        user: User,
        default_training: Training,
    ) -> None:
        """The owner can get their training."""
        api_client.force_authenticate(user=user)
        url = reverse(
            'training_api_v1:training-detail',
            kwargs={'training_id': default_training.pk},
        )

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.OK

        training_data = response.json()

        assert training_data == {
            'id': default_training.pk,
            'status': Training.Status.NOT_STARTED,
            'exercise_type': 'four_step_breathing',
            'first_paused_at': None,
            'cancelled_at': None,
            'created_at': training_data['created_at'],
            'completed_at': None,
        }
        assert training_data['created_at'] is not None

    def test_other_user_gets_not_found(
        self,
        api_client: APIClient,
        other_user: User,
        default_training: Training,
    ) -> None:
        """A training is hidden from users who do not own it."""
        api_client.force_authenticate(user=other_user)
        url = reverse(
            'training_api_v1:training-detail',
            kwargs={'training_id': default_training.pk},
        )

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_unknown_training_returns_not_found(
        self,
        api_client: APIClient,
        user: User,
    ) -> None:
        """An unknown training ID returns not found."""
        api_client.force_authenticate(user=user)
        url = reverse(
            'training_api_v1:training-detail',
            kwargs={'training_id': 999_999},
        )

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_put_patch_and_delete_are_not_allowed(
        self,
        api_client: APIClient,
        user: User,
        default_training: Training,
    ) -> None:
        """The read-only detail endpoint rejects write methods."""
        api_client.force_authenticate(user=user)
        url = reverse(
            'training_api_v1:training-detail',
            kwargs={'training_id': default_training.pk},
        )

        responses = (
            api_client.put(url, data={}, format='json'),
            api_client.patch(url, data={}, format='json'),
            api_client.delete(url),
        )

        assert all(
            response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
            for response in responses
        )
