from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (
    DEFAULT_EXHALE_DURATION_SECONDS,
    DEFAULT_EXHALE_HOLD_DURATION_SECONDS,
    DEFAULT_INHALE_DURATION_SECONDS,
    DEFAULT_INHALE_HOLD_DURATION_SECONDS,
    DEFAULT_ROUND_COUNT,
    MIN_OPTIONAL_HOLD_DURATION_SECONDS,
    MIN_PHASE_DURATION_SECONDS,
    MIN_ROUND_COUNT,
)


class Training(models.Model):
    """Class that describes training session."""

    class Status(models.TextChoices):
        """Model that describes status options."""

        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    status: models.CharField = models.CharField(
        verbose_name='status',
        choices=Status.choices,
        default=Status.NOT_STARTED,
        max_length=20,
    )

    created_at: models.DateTimeField = models.DateTimeField(
        verbose_name='created_at',
        blank=False,
        auto_now_add=True,
    )
    first_paused_at: models.DateTimeField = models.DateTimeField(
        verbose_name='first_paused_at',
        blank=True,
        null=True,
        default=None,
    )
    completed_at: models.DateTimeField = models.DateTimeField(
        verbose_name='completed_at',
        blank=True,
        null=True,
        default=None,
    )
    cancelled_at: models.DateTimeField = models.DateTimeField(
        verbose_name='cancelled_at',
        blank=True,
        null=True,
        default=None,
    )
    user: models.ForeignKey = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trainings',
    )
    exercise: models.ForeignKey = models.ForeignKey(
        to='Exercise',
        on_delete=models.PROTECT,
        related_name='trainings',
    )


class Exercise(models.Model):
    """Basic model of exercise."""

    class ExerciseType(models.TextChoices):
        """Choises for exercise type."""

        FOUR_STEP_BREATHING = (
            'four_step_breathing',
            'Циклическая четырёхфазная тренировка',
        )
        CO2_TABLE = 'co2_table', 'CO₂-таблица'
        O2_TABLE = 'o2_table', 'O₂-таблица'

    exercise_type: models.CharField = models.CharField(
        max_length=100,
        choices=ExerciseType.choices,
    )


class FourStepBreathingExercise(Exercise):
    """Store configuration for a four-step breathing exercise."""

    inhale_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='inhale_duration_seconds',
        blank=False,
        default=DEFAULT_INHALE_DURATION_SECONDS,
        validators=[MinValueValidator(MIN_PHASE_DURATION_SECONDS)],
    )
    inhale_hold_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='inhale_hold_duration_seconds',
        blank=False,
        default=DEFAULT_INHALE_HOLD_DURATION_SECONDS,
        validators=[MinValueValidator(MIN_PHASE_DURATION_SECONDS)],
    )
    exhale_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='exhale_duration_seconds',
        blank=False,
        default=DEFAULT_EXHALE_DURATION_SECONDS,
        validators=[MinValueValidator(MIN_PHASE_DURATION_SECONDS)],
    )
    exhale_hold_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='exhale_hold_duration_seconds',
        blank=False,
        default=DEFAULT_EXHALE_HOLD_DURATION_SECONDS,
        validators=[MinValueValidator(MIN_OPTIONAL_HOLD_DURATION_SECONDS)],
    )
    round_count: models.IntegerField = models.IntegerField(
        verbose_name='round_count',
        blank=False,
        default=DEFAULT_ROUND_COUNT,
        validators=[MinValueValidator(MIN_ROUND_COUNT)],
    )
