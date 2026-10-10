from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from accounts.models import User
from accounts.tokens import (
    check_email_verification_token,
    create_email_verification_token,
)


class EmailVerificationTokenTests(SimpleTestCase):
    """Check email verification token validation."""

    def setUp(self) -> None:
        """Prepare a user without accessing the database."""
        self.user = User(
            pk=7,
            email='alex@example.com',
            is_email_verified=False,
            is_active=False,
        )

    def test_valid_token(self) -> None:
        """Accept a valid token for the same user."""
        token = create_email_verification_token(self.user)

        self.assertTrue(
            check_email_verification_token(self.user, token),
        )

    def test_modified_token(self) -> None:
        """Reject a token with modified signed data."""
        token = create_email_verification_token(self.user)
        modified_token = f'x{token}'

        self.assertFalse(
            check_email_verification_token(self.user, modified_token),
        )

    def test_different_user(self) -> None:
        """Reject a token belonging to another user."""
        token = create_email_verification_token(self.user)
        other_user = User(
            pk=8,
            email=self.user.email,
            is_email_verified=False,
        )

        self.assertFalse(
            check_email_verification_token(other_user, token),
        )

    def test_changed_email(self) -> None:
        """Reject a token after the user email changes."""
        token = create_email_verification_token(self.user)
        self.user.email = 'other@example.com'

        self.assertFalse(
            check_email_verification_token(self.user, token),
        )

    def test_verified_user(self) -> None:
        """Reject a token after email verification."""
        token = create_email_verification_token(self.user)
        self.user.is_email_verified = True

        self.assertFalse(
            check_email_verification_token(self.user, token),
        )

    @override_settings(EMAIL_VERIFICATION_MAX_AGE=60)
    def test_expired_token(self) -> None:
        """Reject a token older than the configured lifetime."""
        with patch('django.core.signing.time.time', return_value=1000):
            token = create_email_verification_token(self.user)

        with patch('django.core.signing.time.time', return_value=1061):
            self.assertFalse(
                check_email_verification_token(self.user, token),
            )

    def test_user_without_pk(self) -> None:
        """Reject token creation for a user without a primary key."""
        user = User(email='new@example.com')

        with self.assertRaises(ValueError):
            create_email_verification_token(user)
