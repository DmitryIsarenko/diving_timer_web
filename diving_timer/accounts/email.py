from django.conf import settings
from django.core.mail import send_mail


def send_welcome_email(to_email: str) -> int:
    """Send a welcome email to email."""
    return send_mail(
        subject='Welcome to Diving Timer!',
        message='Glad to see you!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def send_verification_email(
    to_email: str,
    verification_url: str,
) -> int:
    """Send an email containing the verification link."""
    message = (
        'Welcome to Diving Timer!\n\n'
        'Open the link below, then click Confirm email '
        'to activate your account:\n\n'
        f'{verification_url}\n\n'
        'If you did not create this account, ignore this email.'
    )
    return send_mail(
        subject='Confirm your email for Diving Timer',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
