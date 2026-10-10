from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_EMAIL_LEN
from .managers import CustomUserManager


class User(AbstractUser):
    """Altered model, based on AbstractUser."""

    email = models.EmailField(
        verbose_name='email',
        unique=True,
        blank=False,
        max_length=MAX_EMAIL_LEN,
    )
    username = models.CharField(
        blank=True,
        null=True,
        unique=True,
    )
    is_email_verified: models.BooleanField = models.BooleanField(
        verbose_name='is_email_verified',
        default=False,
    )
    verification_email_last_attempt_at = models.DateTimeField(
        verbose_name='verification_email_last_attempt_at',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        verbose_name='is_active',
        default=False,
    )
    is_staff = models.BooleanField(
        verbose_name='is_staff',
        default=False,
    )
    is_superuser = models.BooleanField(
        verbose_name='is_superuser',
        default=False,
    )
    date_joined = models.DateTimeField(
        verbose_name='date_joined',
        auto_now_add=True,
    )
    modified_at: models.DateTimeField = models.DateTimeField(
        verbose_name='modified at',
        auto_now_add=False,
        auto_now=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: ClassVar[list[str]] = []
    objects: ClassVar[CustomUserManager] = CustomUserManager()  # type: ignore[assignment]

    def save(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Custom user saving method."""
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
