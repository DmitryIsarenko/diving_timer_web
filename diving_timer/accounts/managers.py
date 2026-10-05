from typing import TYPE_CHECKING

from django.contrib.auth.models import BaseUserManager


if TYPE_CHECKING:
    from .models import User


class CustomUserManager(BaseUserManager['User']):
    """Custom user manager."""

    def _create_user(
        self,
        email: str | None,
        password: str | None,
        **extra_fields: object,
    ) -> 'User':
        """Create and save a user with the given username, email, and password."""
        if not email:
            raise ValueError('The given email must be set')
        normalized_email = self.normalize_email(email)
        user = self.model(
            email=normalized_email,
            username=normalized_email,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: object,
    ) -> 'User':
        """User creation method."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: object,
    ) -> 'User':
        """Superuser creation method."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
