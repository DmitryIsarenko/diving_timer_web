from contextlib import nullcontext as does_not_raises

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
import pytest

from accounts.models import User
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
from training.models import Exercise, FourStepBreathingExercise, Training


class TestExerciseModel:
    """Group of test for Exercise."""

    @pytest.mark.parametrize(
        'data',
        (
            pytest.param(
                {'exercise_type': Exercise.ExerciseType.FOUR_STEP_BREATHING},
                id='FOUR_STEP_BREATHING',
            ),
            pytest.param(
                {'exercise_type': Exercise.ExerciseType.CO2_TABLE},
                id='CO2_TABLE',
            ),
            pytest.param(
                {'exercise_type': Exercise.ExerciseType.O2_TABLE},
                id='O2_TABLE',
            ),
        ),
    )
    def test_model_accepts_valid_choices(
        self,
        data: dict[str, str],
    ) -> None:
        """Model accepts valid choices."""
        with does_not_raises():
            exercise = Exercise(**data)
            exercise.full_clean()

    @pytest.mark.parametrize(
        ('data', 'expected_error_code'),
        (
            pytest.param(
                {'exercise_type': 'invalid_exercise_type'},
                'invalid_choice',
                id='invalid-exercise-type',
            ),
            pytest.param(
                {},
                'blank',
                id='missing-exercise-type',
            ),
        ),
    )
    def test_model_rejects_invalid_choices(
        self,
        data: dict[str, str],
        expected_error_code: str,
    ) -> None:
        """Model rejects invalid or not provided exercise_type."""
        with pytest.raises(ValidationError) as exception_info:
            exercise = Exercise(**data)
            exercise.full_clean()

        error_code = exception_info.value.error_dict['exercise_type'][0].code
        assert error_code == expected_error_code


class TestFourStepBreathingExerciseModel:
    """Group of tests for FourStepBreathingExercise."""

    def test_model_uses_defaults(
        self,
        default_4_step_exercise: FourStepBreathingExercise,
    ) -> None:
        """Creating exercise without durations gives it defaults."""
        assert (
            default_4_step_exercise.exhale_duration_seconds
            == DEFAULT_EXHALE_DURATION_SECONDS
        )
        assert (
            default_4_step_exercise.exhale_hold_duration_seconds
            == DEFAULT_EXHALE_HOLD_DURATION_SECONDS
        )
        assert (
            default_4_step_exercise.inhale_duration_seconds
            == DEFAULT_INHALE_DURATION_SECONDS
        )
        assert (
            default_4_step_exercise.inhale_hold_duration_seconds
            == DEFAULT_INHALE_HOLD_DURATION_SECONDS
        )
        assert default_4_step_exercise.round_count == DEFAULT_ROUND_COUNT

    @pytest.mark.parametrize(
        ('field_name', 'min_value'),
        (
            ('inhale_duration_seconds', MIN_PHASE_DURATION_SECONDS),
            ('inhale_hold_duration_seconds', MIN_PHASE_DURATION_SECONDS),
            ('exhale_duration_seconds', MIN_PHASE_DURATION_SECONDS),
            (
                'exhale_hold_duration_seconds',
                MIN_OPTIONAL_HOLD_DURATION_SECONDS,
            ),
            ('round_count', MIN_ROUND_COUNT),
        ),
    )
    def test_model_accept_min_values(
        self,
        field_name: str,
        min_value: int,
    ) -> None:
        """Model accepts minimum values."""
        with does_not_raises():
            training = FourStepBreathingExercise(
                exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
            )
            setattr(training, field_name, min_value)
            training.full_clean()

    @pytest.mark.parametrize(
        ('field_name', 'invalid_value', 'expected_error_code'),
        (
            (
                'inhale_duration_seconds',
                MIN_PHASE_DURATION_SECONDS - 1,
                'min_value',
            ),
            (
                'inhale_hold_duration_seconds',
                MIN_PHASE_DURATION_SECONDS - 1,
                'min_value',
            ),
            (
                'exhale_duration_seconds',
                MIN_PHASE_DURATION_SECONDS - 1,
                'min_value',
            ),
            (
                'exhale_hold_duration_seconds',
                MIN_OPTIONAL_HOLD_DURATION_SECONDS - 1,
                'min_value',
            ),
            ('round_count', MIN_ROUND_COUNT - 1, 'min_value'),
        ),
    )
    def test_model_rejects_less_than_min_values(
        self,
        start_four_step_breath_exercise_data: dict[str, str | int],
        field_name: str,
        invalid_value: int,
        expected_error_code: str,
    ) -> None:
        """Model rejects values below the minimum."""
        data = start_four_step_breath_exercise_data
        data[field_name] = invalid_value

        with pytest.raises(ValidationError) as exception_info:
            training = FourStepBreathingExercise(**data)
            training.full_clean()

        error_code = exception_info.value.error_dict[field_name][0].code
        assert error_code == expected_error_code

    def test_multitable_inheritance(
        self,
        default_4_step_exercise: FourStepBreathingExercise,
    ) -> None:
        """Saved child has a parent record with access to the child."""
        parent_exercise = Exercise.objects.get(pk=default_4_step_exercise.pk)

        assert type(parent_exercise) is Exercise
        assert (
            parent_exercise.exercise_type
            == Exercise.ExerciseType.FOUR_STEP_BREATHING
        )

        child_exercise = getattr(parent_exercise, 'fourstepbreathingexercise')  # noqa: B009
        assert child_exercise == default_4_step_exercise


class TestTrainingModel:
    """Group of test for Training model."""

    def test_model_defaults(self, default_training: Training) -> None:
        """New training has expected initial state."""
        assert default_training.status == Training.Status.NOT_STARTED
        assert default_training.created_at is not None
        assert default_training.cancelled_at is None
        assert default_training.completed_at is None
        assert default_training.first_paused_at is None

    def test_model_stores_user_and_exercise(
        self,
        user: User,
        default_4_step_exercise: FourStepBreathingExercise,
        default_training: Training,
    ) -> None:
        """Training stores its user and exercise."""
        assert default_training.user == user
        assert default_training.exercise == default_4_step_exercise

    @pytest.mark.parametrize(
        'status',
        (
            Training.Status.NOT_STARTED,
            Training.Status.CANCELLED,
            Training.Status.COMPLETED,
            Training.Status.IN_PROGRESS,
            Training.Status.PAUSED,
        ),
    )
    def test_model_accepts_valid_statuses(
        self,
        status: str,
        default_training: Training,
    ) -> None:
        """Training accepts valid statuses."""
        default_training.status = status
        default_training.full_clean()

    def test_model_rejects_invalid_status(
        self,
        default_training: Training,
    ) -> None:
        """Training rejects an invalid status."""
        default_training.status = 'invalid_status'
        with pytest.raises(ValidationError) as exception_info:
            default_training.full_clean()

        error_code = exception_info.value.error_dict['status'][0].code
        assert error_code == 'invalid_choice'

    def test_user_trainings_related_name(
        self,
        user: User,
        default_training: Training,
    ) -> None:
        """User provides access to related trainings."""
        trainings = getattr(user, 'trainings')  # noqa: B009
        assert list(trainings.all()) == [default_training]

    def test_exercise_trainings_related_name(
        self,
        default_4_step_exercise: FourStepBreathingExercise,
        default_training: Training,
    ) -> None:
        """Exercise provides access to related trainings."""
        trainings = getattr(default_4_step_exercise, 'trainings')  # noqa: B009
        assert list(trainings.all()) == [default_training]

    def test_deleting_user_cascades_to_training(
        self,
        user: User,
        default_training: Training,
        default_4_step_exercise: FourStepBreathingExercise,
    ) -> None:
        """Deleting a user deletes their training."""
        training_pk = default_training.pk
        exercise_pk = default_4_step_exercise.pk

        user.delete()

        assert not Training.objects.filter(pk=training_pk).exists()
        assert Exercise.objects.filter(pk=exercise_pk).exists()

    def test_deleting_used_exercise_is_protected(
        self,
        default_training: Training,
        default_4_step_exercise: FourStepBreathingExercise,
    ) -> None:
        """An exercise used by a training cannot be deleted."""
        training_pk = default_training.pk
        exercise_pk = default_4_step_exercise.pk

        with pytest.raises(ProtectedError):
            default_4_step_exercise.delete()

        assert Training.objects.filter(pk=training_pk).exists()
        assert Exercise.objects.filter(pk=exercise_pk).exists()
