from typing import cast

import pytest

from accounts.models import User
from training.models import Exercise, FourStepBreathingExercise, Training


@pytest.fixture
def start_four_step_breath_exercise_data() -> dict[str, str]:
    """Valid form data from form."""
    return {
        'inhale_duration_seconds': '5',
        'inhale_hold_duration_seconds': '20',
        'exhale_duration_seconds': '4',
        'exhale_hold_duration_seconds': '2',
        'round_count': '5',
    }


@pytest.fixture
def default_4_step_exercise(db: None) -> FourStepBreathingExercise:
    """Creates 4-step exercise with default params."""
    exercise: FourStepBreathingExercise = cast(
        FourStepBreathingExercise,
        FourStepBreathingExercise.objects.create(
            exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
        ),
    )
    return exercise


@pytest.fixture
def default_training(
    user: User,
    default_4_step_exercise: FourStepBreathingExercise,
) -> Training:
    """Create a training with default state."""
    return Training.objects.create(user=user, exercise=default_4_step_exercise)
