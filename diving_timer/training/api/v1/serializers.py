from rest_framework import serializers

from training.models import Training


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
            'first_paused_at',
            'cancelled_at',
            'created_at',
            'completed_at',
        )
        read_only_fields = fields
