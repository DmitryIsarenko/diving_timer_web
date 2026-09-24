from django import forms

from .constants import (
    MIN_OPTIONAL_HOLD_DURATION_SECONDS,
    MIN_PHASE_DURATION_SECONDS,
    MIN_ROUND_COUNT,
)


class FourStepBreathingExerciseStartForm(forms.Form):
    """Form for a entering data before starting exercise of 4-step breating."""

    inhale_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=MIN_PHASE_DURATION_SECONDS
    )
    inhale_hold_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=MIN_PHASE_DURATION_SECONDS
    )
    exhale_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=MIN_PHASE_DURATION_SECONDS
    )
    exhale_hold_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=MIN_OPTIONAL_HOLD_DURATION_SECONDS
    )
    round_count: forms.IntegerField = forms.IntegerField(
        min_value=MIN_ROUND_COUNT
    )


class TrainingStatusActionForm(forms.Form):
    """Form to send data of switching states of an exercise."""

    statuses = [
        ('pause', 'Pause'),
        ('resume', 'Resume'),
        ('complete', 'Complete'),
        ('cancel', 'Cancel'),
    ]

    action = forms.ChoiceField(choices=statuses)
