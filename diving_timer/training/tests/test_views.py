from http import HTTPStatus

from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects

from training.constants import (
    DEFAULT_EXHALE_DURATION_SECONDS,
    DEFAULT_EXHALE_HOLD_DURATION_SECONDS,
    DEFAULT_INHALE_DURATION_SECONDS,
    DEFAULT_INHALE_HOLD_DURATION_SECONDS,
    DEFAULT_ROUND_COUNT,
    MIN_OPTIONAL_HOLD_DURATION_SECONDS,
    MIN_PHASE_DURATION_SECONDS,
    MIN_ROUND_COUNT,
)
from training.models import FourStepBreathingExercise, Training


class TestPublicTrainingViews:
    """Tests for public training pages."""

    @pytest.mark.parametrize(
        ('url_name', 'template_name'),
        (
            ('index', 'training/index.html'),
            ('trainings', 'training/trainings.html'),
            ('four_step_breathing', 'training/four_step_breathing.html'),
        ),
    )
    def test_get_renders_expected_template(
        self,
        client: Client,
        url_name: str,
        template_name: str,
    ) -> None:
        """Public GET views render their expected templates."""
        response = client.get(reverse(url_name))
        template_names = [template.name for template in response.templates]
        assert response.status_code == HTTPStatus.OK
        assert template_name in template_names

    def test_four_step_page_contains_configuration(
        self,
        client: Client,
    ) -> None:
        """Four-step page contains defaults and minimums."""
        response = client.get(reverse('four_step_breathing'))

        assert response.status_code == HTTPStatus.OK

        assert response.context['four_step_defaults'] == {
            'inhale_duration_seconds': DEFAULT_INHALE_DURATION_SECONDS,
            'inhale_hold_duration_seconds': (
                DEFAULT_INHALE_HOLD_DURATION_SECONDS
            ),
            'exhale_duration_seconds': DEFAULT_EXHALE_DURATION_SECONDS,
            'exhale_hold_duration_seconds': (
                DEFAULT_EXHALE_HOLD_DURATION_SECONDS
            ),
            'round_count': DEFAULT_ROUND_COUNT,
        }

        assert response.context['four_step_minimums'] == {
            'phase_duration_seconds': MIN_PHASE_DURATION_SECONDS,
            'optional_hold_duration_seconds': (
                MIN_OPTIONAL_HOLD_DURATION_SECONDS
            ),
            'round_count': MIN_ROUND_COUNT,
        }


class TestStartFourStepBreathingExerciseView:
    """Tests for starting a four-step exercise."""

    def test_anonymous_user_is_redirected_to_login(
        self,
        client: Client,
        start_four_step_breath_exercise_data: dict[str, str],
    ) -> None:
        """Anonymous user cannot start a saved training."""
        url = reverse('start_four_step_breathing_exercise')
        response = client.post(
            url,
            data=start_four_step_breath_exercise_data,
        )

        expected_url = f'{reverse("login")}?next={url}'

        assert response.url == expected_url
        assert response.status_code == HTTPStatus.FOUND

    def test_get_is_not_allowed(self, user_client: Client) -> None:
        """Start endpoint accepts only POST requests."""
        response = user_client.get(
            reverse('start_four_step_breathing_exercise')
        )

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
        assert response.headers['Allow'] == 'POST'

    def test_post_creates_two_models(
        self,
        user_client: Client,
        start_four_step_breath_exercise_data: dict[str, str],
    ) -> None:
        """Successful POST creates two models."""
        url = reverse('start_four_step_breathing_exercise')
        response = user_client.post(
            url,
            data=start_four_step_breath_exercise_data,
        )

        assert response.status_code == HTTPStatus.CREATED
        training_pk = response.json()['training_id']
        training = Training.objects.get(pk=training_pk)
        exercise = FourStepBreathingExercise.objects.get(
            pk=training.exercise_id
        )

        assert training.status == Training.Status.IN_PROGRESS
        assert exercise.round_count == DEFAULT_ROUND_COUNT

    def test_post_with_invalid_data_creates_nothing(
        self,
        user_client: Client,
        start_four_step_breath_exercise_data: dict[str, str],
    ) -> None:
        """Invalid POST returns errors and creates nothing."""
        trainings_count_before = Training.objects.count()
        exercises_count_before = FourStepBreathingExercise.objects.count()

        url = reverse('start_four_step_breathing_exercise')
        start_four_step_breath_exercise_data['inhale_duration_seconds'] = '-1'
        response = user_client.post(
            url,
            data=start_four_step_breath_exercise_data,
        )

        trainings_count_after = Training.objects.count()
        exercises_count_after = FourStepBreathingExercise.objects.count()

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert trainings_count_before == trainings_count_after
        assert exercises_count_before == exercises_count_after


class TestUpdateTrainingStatusView:
    """Collection of test for update_training_status view logic."""

    def test_anonymous_user_redirected(
        self, client: Client, default_training: Training
    ) -> None:
        """Anonymous user redirected to index page."""
        status_before = default_training.status
        url = reverse(
            'update_training_status',
            kwargs={'training_id': default_training.pk},
        )
        response = client.post(url)
        status_after = default_training.status

        expected_url = f'{reverse("login")}?next={url}'

        assertRedirects(response, expected_url)
        assert response.status_code == HTTPStatus.FOUND
        assert status_before == status_after

    def test_method_get_not_allowed(
        self,
        user_client: Client,
        default_training: Training,
    ) -> None:
        """GET method not allowed."""
        status_before = default_training.status
        url = reverse(
            'update_training_status',
            kwargs={'training_id': default_training.pk},
        )

        response = user_client.get(url)
        status_after = default_training.status

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
        assert status_before == status_after

    def test_changing_another_user_training_is_not_allowed(
        self,
        other_user_client: Client,
        default_training: Training,
    ) -> None:
        """Changing other user`s training is not allowed."""
        status_before = default_training.status
        url = reverse(
            'update_training_status',
            kwargs={'training_id': default_training.pk},
        )

        response = other_user_client.post(url, data={'action': 'cancel'})
        default_training.refresh_from_db()
        status_after = default_training.status

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert status_before == status_after

    @pytest.mark.parametrize(
        (
            'initial_status',
            'action',
            'expected_status',
            'expected_http_status',
            'timestamp_field',
        ),
        (
            (
                Training.Status.IN_PROGRESS,
                'pause',
                Training.Status.PAUSED,
                HTTPStatus.OK,
                'first_paused_at',
            ),
            (
                Training.Status.IN_PROGRESS,
                'complete',
                Training.Status.COMPLETED,
                HTTPStatus.OK,
                'completed_at',
            ),
            (
                Training.Status.IN_PROGRESS,
                'cancel',
                Training.Status.CANCELLED,
                HTTPStatus.OK,
                'cancelled_at',
            ),
            (
                Training.Status.PAUSED,
                'resume',
                Training.Status.IN_PROGRESS,
                HTTPStatus.OK,
                None,
            ),
            (
                Training.Status.PAUSED,
                'cancel',
                Training.Status.CANCELLED,
                HTTPStatus.OK,
                'cancelled_at',
            ),
        ),
    )
    def test_acceptable_changing_statuses(
        self,
        user_client: Client,
        default_training: Training,
        initial_status: str,
        action: str,
        expected_status: str,
        expected_http_status: str,
        timestamp_field: str | None,
    ) -> None:
        """Only acceptable transitions are allowed."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])

        url = reverse(
            'update_training_status',
            kwargs={'training_id': default_training.pk},
        )
        response = user_client.post(url, data={'action': action})

        default_training.refresh_from_db()

        assert default_training.status == expected_status
        assert response.status_code == expected_http_status

        if timestamp_field:
            assert getattr(default_training, timestamp_field) is not None

    @pytest.mark.parametrize(
        (
            'initial_status',
            'action',
            'expected_status',
            'expected_http_status',
        ),
        (
            (
                Training.Status.PAUSED,
                'complete',
                Training.Status.PAUSED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.NOT_STARTED,
                'pause',
                Training.Status.NOT_STARTED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.NOT_STARTED,
                'resume',
                Training.Status.NOT_STARTED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.NOT_STARTED,
                'complete',
                Training.Status.NOT_STARTED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.NOT_STARTED,
                'cancel',
                Training.Status.NOT_STARTED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.COMPLETED,
                'pause',
                Training.Status.COMPLETED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.COMPLETED,
                'resume',
                Training.Status.COMPLETED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.COMPLETED,
                'complete',
                Training.Status.COMPLETED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.COMPLETED,
                'cancel',
                Training.Status.COMPLETED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.CANCELLED,
                'pause',
                Training.Status.CANCELLED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.CANCELLED,
                'resume',
                Training.Status.CANCELLED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.CANCELLED,
                'complete',
                Training.Status.CANCELLED,
                HTTPStatus.CONFLICT,
            ),
            (
                Training.Status.CANCELLED,
                'cancel',
                Training.Status.CANCELLED,
                HTTPStatus.CONFLICT,
            ),
        ),
    )
    def test_not_acceptable_changing_statuses(
        self,
        user_client: Client,
        default_training: Training,
        initial_status: str,
        action: str,
        expected_status: str,
        expected_http_status: str,
    ) -> None:
        """Only acceptable transitions are allowed."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])

        url = reverse(
            'update_training_status',
            kwargs={'training_id': default_training.pk},
        )
        response = user_client.post(url, data={'action': action})

        default_training.refresh_from_db()

        assert default_training.status == expected_status
        assert response.status_code == expected_http_status


class TestDeleteTrainingView:
    """Test for deletion logic."""

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.CANCELLED,
            Training.Status.COMPLETED,
        ),
    )
    def test_cancelled_or_completed_are_deletable(
        self,
        default_training: Training,
        user_client: Client,
        initial_status: str,
    ) -> None:
        """Only complete or cancelled training can be deleted."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])

        training_id = default_training.pk

        url = reverse('delete_training', kwargs={'training_id': training_id})
        response = user_client.post(url)

        assert Training.objects.filter(pk=training_id).count() == 0
        assert response.status_code == HTTPStatus.FOUND

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.NOT_STARTED,
            Training.Status.IN_PROGRESS,
            Training.Status.PAUSED,
        ),
    )
    def test_not_cancelled_or_completed_are_not_deletable(
        self,
        default_training: Training,
        user_client: Client,
        initial_status: str,
    ) -> None:
        """Only complete or cancelled training can be deleted."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])

        training_id = default_training.pk

        url = reverse('delete_training', kwargs={'training_id': training_id})
        response = user_client.post(url)

        assert Training.objects.filter(pk=training_id).count() == 1
        assert response.status_code == HTTPStatus.CONFLICT

    def test_redirect_on_deletion(
        self,
        default_training: Training,
        user_client: Client,
    ) -> None:
        """Redirects to exercise page."""
        default_training.status = Training.Status.COMPLETED
        default_training.save(update_fields=['status'])

        training_id = default_training.pk

        url = reverse('delete_training', kwargs={'training_id': training_id})
        response = user_client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(
            response,
            reverse(
                'exercise_statistics_by_exercise',
                kwargs={
                    'exercise_type': default_training.exercise.exercise_type
                },
            ),
        )

    def test_cannot_delete_other_users_training(
        self,
        other_user_client: Client,
        default_training: Training,
    ) -> None:
        """Another user cannot delete a training."""
        default_training.status = Training.Status.COMPLETED
        default_training.save(update_fields=['status'])

        response = other_user_client.post(
            reverse(
                'delete_training',
                kwargs={'training_id': default_training.pk},
            )
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Training.objects.filter(pk=default_training.pk).exists()


class TestTrainingOwnership:
    """Group of test for testing ownerships."""

    def test_general_statistics_excludes_other_users_trainings(
        self,
        default_training: Training,
        other_user_client: Client,
    ) -> None:
        """Cannot see others training details."""
        url = reverse('exercise_statistics')
        response = other_user_client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context['total_trainings'] == 0

    def test_cannot_see_others_training_by_training_details(
        self,
        default_training: Training,
        other_user_client: Client,
    ) -> None:
        """Cannot see others training details."""
        url = reverse(
            'exercise_statistics_by_training',
            kwargs={'training_id': default_training.pk},
        )
        response = other_user_client.get(url)

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_cannot_see_others_training_by_exercise_details(
        self,
        default_training: Training,
        other_user_client: Client,
    ) -> None:
        """Cannot see others training details."""
        url = reverse(
            'exercise_statistics_by_exercise',
            kwargs={'exercise_type': default_training.exercise.exercise_type},
        )
        response = other_user_client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context['total_trainings'] == 0


class TestCancellingTrainings:
    """Collection for testing cancelling trainings."""

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.NOT_STARTED,
            Training.Status.IN_PROGRESS,
            Training.Status.PAUSED,
        ),
    )
    def test_cancel_training_from_training_details(
        self,
        default_training: Training,
        user_client: Client,
        initial_status: str,
    ) -> None:
        """Cancel from training details."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])
        training_id = default_training.pk

        url = reverse(
            'cancel_training_from_training_details',
            kwargs={'training_id': training_id},
        )
        response = user_client.post(url)
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.FOUND
        assert default_training.status == Training.Status.CANCELLED
        assert default_training.cancelled_at is not None

        assertRedirects(
            response,
            reverse(
                'exercise_statistics_by_training',
                kwargs={'training_id': training_id},
            ),
            fetch_redirect_response=False,
        )

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.NOT_STARTED,
            Training.Status.IN_PROGRESS,
            Training.Status.PAUSED,
        ),
    )
    def test_cancel_training_from_trainings_by_exercise(
        self,
        default_training: Training,
        user_client: Client,
        initial_status: str,
    ) -> None:
        """Cancel from exercise list."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])
        exercise_type = default_training.exercise.exercise_type

        url = reverse(
            'cancel_training_from_trainings_by_exercise',
            kwargs={
                'training_id': default_training.pk,
                'exercise_type': exercise_type,
            },
        )
        response = user_client.post(url)
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.FOUND
        assert default_training.status == Training.Status.CANCELLED
        assert default_training.cancelled_at is not None

        assertRedirects(
            response,
            reverse(
                'exercise_statistics_by_exercise',
                kwargs={'exercise_type': exercise_type},
            ),
            fetch_redirect_response=False,
        )

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.COMPLETED,
            Training.Status.CANCELLED,
        ),
    )
    def test_cannot_cancel_final_training_from_details(
        self,
        user_client: Client,
        default_training: Training,
        initial_status: str,
    ) -> None:
        """Test_cannot_cancel_final_training_from_details."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])
        training_id = default_training.pk

        url = reverse(
            'cancel_training_from_training_details',
            kwargs={'training_id': training_id},
        )
        response = user_client.post(url)
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.CONFLICT
        assert default_training.status == initial_status

    @pytest.mark.parametrize(
        'initial_status',
        (
            Training.Status.COMPLETED,
            Training.Status.CANCELLED,
        ),
    )
    def test_cannot_cancel_final_training_from_exercise_list(
        self,
        user_client: Client,
        default_training: Training,
        initial_status: str,
    ) -> None:
        """Test_cannot_cancel_final_training_from_exercise_list."""
        default_training.status = initial_status
        default_training.save(update_fields=['status'])
        exercise_type = default_training.exercise.exercise_type
        url = reverse(
            'cancel_training_from_trainings_by_exercise',
            kwargs={
                'training_id': default_training.pk,
                'exercise_type': exercise_type,
            },
        )
        response = user_client.post(url)
        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.CONFLICT
        assert default_training.status == initial_status

    def test_cannot_cancel_other_users_training_from_details(
        self,
        default_training: Training,
        other_user_client: Client,
    ) -> None:
        """Another user cannot cancel training from its details."""
        initial_status = default_training.status
        url = reverse(
            'cancel_training_from_training_details',
            kwargs={'training_id': default_training.pk},
        )

        response = other_user_client.post(url)

        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert default_training.status == initial_status
        assert default_training.cancelled_at is None

    def test_cannot_cancel_other_users_training_from_exercise_list(
        self,
        default_training: Training,
        other_user_client: Client,
    ) -> None:
        """Another user cannot cancel training from an exercise list."""
        initial_status = default_training.status
        url = reverse(
            'cancel_training_from_trainings_by_exercise',
            kwargs={
                'exercise_type': (default_training.exercise.exercise_type),
                'training_id': default_training.pk,
            },
        )

        response = other_user_client.post(url)

        default_training.refresh_from_db()

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert default_training.status == initial_status
        assert default_training.cancelled_at is None

    def test_user_can_see_own_training_details(
        self,
        default_training: Training,
        default_4_step_exercise: FourStepBreathingExercise,
        user_client: Client,
    ) -> None:
        """A user can see their own training details."""
        url = reverse(
            'exercise_statistics_by_training',
            kwargs={'training_id': default_training.pk},
        )
        expected_duration = (
            default_4_step_exercise.inhale_duration_seconds
            + default_4_step_exercise.inhale_hold_duration_seconds
            + default_4_step_exercise.exhale_duration_seconds
            + default_4_step_exercise.exhale_hold_duration_seconds
        ) * default_4_step_exercise.round_count

        response = user_client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context['training'] == default_training
        assert response.context['exercise'] == default_4_step_exercise
        assert response.context['planned_duration'] == expected_duration
