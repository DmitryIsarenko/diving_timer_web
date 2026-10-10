from django.conf import settings
from django.core import signing

from .models import User


EMAIL_VERIFICATION_SALT = 'accounts.email-verification'


def create_email_verification_token(user: User) -> str:
    """Create a signed email verification token."""
    if user.pk is None:
        raise ValueError('User must be saved before creating a token.')
    return signing.dumps(
        {
            'user_id': user.pk,
            'email': user.email,
        },
        salt=EMAIL_VERIFICATION_SALT,
    )


def check_email_verification_token(
    user: User,
    token: str,
) -> bool:
    """Check token signature, age, and current user state."""
    if user.pk is None or user.is_email_verified:
        return False

    try:
        payload = signing.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=settings.EMAIL_VERIFICATION_MAX_AGE,
        )
    except signing.BadSignature:
        return False
    return payload == {
        'user_id': user.pk,
        'email': user.email,
    }
