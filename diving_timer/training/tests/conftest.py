import pytest


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