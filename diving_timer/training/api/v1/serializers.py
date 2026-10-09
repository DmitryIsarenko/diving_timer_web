from rest_framework import serializers

from training.models import FourStepBreathingExercise, Training


class TrainingSerializer(serializers.ModelSerializer):
    """Training serializer."""

    exercise_type = serializers.CharField(
        source='exercise.exercise_type',
        read_only=True,
    )

    class Meta:
        """Meta class."""

        model = Training
        fields = (
            'id',
            'status',
            'exercise_type',
            'created_at',
            'first_paused_at',
            'cancelled_at',
            'completed_at',
        )
        read_only_fields = fields


class TrainingActionSerializer(serializers.Serializer):
    """Validate actions."""

    statuses = [
        'pause',
        'resume',
        'complete',
        'cancel',
    ]
    action = serializers.ChoiceField(choices=statuses)


class FourStepBreathingExerciseSerializer(serializers.ModelSerializer):
    """Serialize four-step breathing exercise settings."""

    class Meta:
        """Meta-class."""

        model = FourStepBreathingExercise
        fields = (
            'id',
            'inhale_duration_seconds',
            'inhale_hold_duration_seconds',
            'exhale_duration_seconds',
            'exhale_hold_duration_seconds',
            'round_count',
        )
        read_only_fields = ('id',)


class FourStepBreathingTrainingCreateSerializer(serializers.ModelSerializer):
    """Validate four-step breathing training data for creation."""

    class Meta:
        """Meta-class."""

        model = FourStepBreathingExercise
        fields = (
            'inhale_duration_seconds',
            'inhale_hold_duration_seconds',
            'exhale_duration_seconds',
            'exhale_hold_duration_seconds',
            'round_count',
        )


class FourStepBreathingTrainingSerializer(serializers.ModelSerializer):
    """Serialize a training with its four-step breathing exercise."""

    exercise = FourStepBreathingExerciseSerializer(
        source='exercise.fourstepbreathingexercise',
        read_only=True,
    )
    exercise_type = serializers.CharField(
        source='exercise.exercise_type',
        read_only=True,
    )

    class Meta:
        """Meta-class."""

        model = Training
        fields = (
            'id',
            'status',
            'exercise_type',
            'exercise',
            'created_at',
            'first_paused_at',
            'cancelled_at',
            'completed_at',
        )
        read_only_fields = fields
