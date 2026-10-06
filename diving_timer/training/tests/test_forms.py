import pytest

from training.forms import (
    FourStepBreathingExerciseStartForm,
    TrainingStatusActionForm,
)


class TestStartFourStepBreathingExerciseForm:
    """Testing FourStepBreathingExercise Form."""

    def test_start_form_accepts_valid_data(
        self,
        start_four_step_breath_exercise_data: dict[str, str],
    ) -> None:
        """Start form accept valid data."""
        form = FourStepBreathingExerciseStartForm(
            data=start_four_step_breath_exercise_data
        )
        assert form.is_valid(), form.errors

        cleaned_data = form.cleaned_data
        normalized_data = {
            key: int(value)
            for key, value in start_four_step_breath_exercise_data.items()
        }
        assert cleaned_data == normalized_data

    @pytest.mark.parametrize(
        ('field_name', 'min_value'),
        (
            ('inhale_duration_seconds', 1),
            ('inhale_hold_duration_seconds', 1),
            ('exhale_duration_seconds', 1),
            ('exhale_hold_duration_seconds', 0),
            ('round_count', 1),
        ),
    )
    def test_start_form_accepts_minimum_values(
        self,
        start_four_step_breath_exercise_data: dict[str, str],
        field_name: str,
        min_value: int,
    ) -> None:
        """Form accept minimum values."""
        start_four_step_breath_exercise_data[field_name] = str(min_value)
        form = FourStepBreathingExerciseStartForm(
            data=start_four_step_breath_exercise_data
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data[field_name] == min_value

    @pytest.mark.parametrize(
        ('field_name', 'invalid_value'),
        (
            ('inhale_duration_seconds', 0),
            ('inhale_hold_duration_seconds', 0),
            ('exhale_duration_seconds', 0),
            ('exhale_hold_duration_seconds', -1),
            ('round_count', 0),
        ),
    )
    def test_start_form_rejects_less_than_minimum_values(
        self,
        start_four_step_breath_exercise_data: dict[str, str],
        field_name: str,
        invalid_value: int,
    ) -> None:
        """Form rejects less than minimum values."""
        start_four_step_breath_exercise_data[field_name] = str(invalid_value)
        form = FourStepBreathingExerciseStartForm(
            data=start_four_step_breath_exercise_data
        )
        assert not form.is_valid()
        assert form.has_error(field_name, code='min_value')

    @pytest.mark.parametrize(
        ('field_name',),
        (
            ('inhale_duration_seconds',),
            ('inhale_hold_duration_seconds',),
            ('exhale_duration_seconds',),
            ('exhale_hold_duration_seconds',),
            ('round_count',),
        ),
    )
    @pytest.mark.parametrize(
        ('invalid_value', 'error_code'),
        (
            pytest.param('abc', 'invalid', id='not-a-number'),
            pytest.param('1.5', 'invalid', id='fractional-number'),
            pytest.param('', 'required', id='empty-value'),
        ),
    )
    def test_start_form_rejects_invalid_values(
        self,
        start_four_step_breath_exercise_data: dict[str, str],
        field_name: str,
        invalid_value: str,
        error_code: str,
    ) -> None:
        """Start form rejects float, chars and empty values."""
        start_four_step_breath_exercise_data[field_name] = invalid_value
        form = FourStepBreathingExerciseStartForm(
            data=start_four_step_breath_exercise_data
        )

        assert not form.is_valid()
        assert form.has_error(field_name, code=error_code)

    @pytest.mark.parametrize(
        ('field_name',),
        (
            ('inhale_duration_seconds',),
            ('inhale_hold_duration_seconds',),
            ('exhale_duration_seconds',),
            ('exhale_hold_duration_seconds',),
            ('round_count',),
        ),
    )
    def test_form_require_every_field(
        self,
        field_name: str,
        start_four_step_breath_exercise_data: dict[str, str],
    ) -> None:
        """Form requires every field."""
        start_four_step_breath_exercise_data.pop(field_name)
        form = FourStepBreathingExerciseStartForm(
            data=start_four_step_breath_exercise_data
        )
        assert not form.is_valid()

        assert form.has_error(field_name, 'required')


class TestTrainingStatusActionForm:
    """Test validation of training actions."""

    @pytest.mark.parametrize(
        'action',
        (
            'pause',
            'resume',
            'complete',
            'cancel',
        ),
    )
    def test_action_form_accepts_valid_actions(self, action: str) -> None:
        """Status action form accepts valid actions."""
        form = TrainingStatusActionForm(data={'action': action})
        assert form.is_valid(), form.errors
        assert form.cleaned_data == {'action': action}

    def test_action_form_rejects_invalid_actions(self) -> None:
        """Status action form rejects invalid actions."""
        invalid_action = 'invalid_action'
        form = TrainingStatusActionForm(data={'action': invalid_action})
        assert not form.is_valid()
        assert form.has_error('action', 'invalid_choice')

    @pytest.mark.parametrize(
        'data',
        (
            pytest.param({}, id='missing-action'),
            pytest.param({'action': ''}, id='empty-action'),
        ),
    )
    def test_action_form_requires_action(self, data: dict) -> None:
        """Status action form requires an action."""
        form = TrainingStatusActionForm(data=data)
        assert not form.is_valid()
        assert form.has_error('action', 'required')
