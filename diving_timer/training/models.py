from django.conf import settings
from django.db import models


class Training(models.Model):
    """Class that describes training session."""

    STATUS_CHOICES = [
        ('not_started', 'not_started'),
        ('in_progress', 'in_progress'),
        ('paused', 'paused'),
        ('completed', 'completed'),
        ('cancelled', 'cancelled'),
    ]

    status: models.CharField = models.CharField(
        verbose_name='status',
        choices=STATUS_CHOICES,
        default='not_started',
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


class FourStepBreathingExercise(Exercise):
    """Store configuration for a four-step breathing exercise."""

    inhale_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='inhale_duration_seconds', blank=False, default=5
    )
    inhale_hold_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='inhale_hold_duration_seconds', blank=False, default=10
    )
    exhale_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='exhale_duration_seconds', blank=False, default=5
    )
    exhale_hold_duration_seconds: models.IntegerField = models.IntegerField(
        verbose_name='exhale_hold_duration_seconds', blank=False, default=0
    )
    round_count: models.IntegerField = models.IntegerField(
        verbose_name='round_count', blank=False, default=1
    )
