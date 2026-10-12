from accounts.email import send_verification_email, send_welcome_email
from diving_timer.celery import app


@app.task
def send_welcome(to_email: str) -> None:
    """Test send welcome email by celery."""
    send_welcome_email(to_email=to_email)


@app.task
def send_verification_email_by_celery(
    to_email: str,
    verification_url: str,
) -> None:
    """Send verificaiton email by celery."""
    send_verification_email(
        to_email=to_email,
        verification_url=verification_url,
    )
