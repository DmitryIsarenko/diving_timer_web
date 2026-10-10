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
