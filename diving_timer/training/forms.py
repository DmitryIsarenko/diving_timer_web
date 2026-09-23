from django import forms


class FourStepBreathingExerciseStartForm(forms.Form):
    """Form for a entering data before starting exercise of 4-step breating."""

    inhale_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=1
    )
    inhale_hold_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=1
    )
    exhale_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=1
    )
    exhale_hold_duration_seconds: forms.IntegerField = forms.IntegerField(
        min_value=0
    )
    round_count: forms.IntegerField = forms.IntegerField(min_value=1)
