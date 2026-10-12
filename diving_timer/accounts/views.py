from datetime import timedelta
from functools import partial
from http import HTTPStatus

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .constants import VERIFICATION_EMAIL_RESEND_INTERVAL
from .forms import RegistrationForm
from .models import User
from .tasks import send_verification_email_by_celery
from .tokens import (
    check_email_verification_token,
    create_email_verification_token,
)


def register(request: HttpRequest) -> HttpResponse:
    """Register a new user."""
    if request.method == 'GET':
        form = RegistrationForm()
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.verification_email_last_attempt_at = timezone.now()
            user.save()

            request.session['pending_verification_user_id'] = user.pk

            token = create_email_verification_token(user=user)
            verification_path = reverse(
                'verify_email',
                kwargs={
                    'user_id': user.pk,
                    'token': token,
                },
            )
            verification_url = f'{settings.SITE_BASE_URL}{verification_path}'

            transaction.on_commit(
                partial(
                    send_verification_email_by_celery.delay,
                    to_email=user.email,
                    verification_url=verification_url,
                ),
                robust=True,
            )

            return render(request, 'accounts/verification_pending.html')

        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    return HttpResponseNotAllowed(['GET', 'POST'])


def verify_email(
    request: HttpRequest, user_id: int, token: str
) -> HttpResponse:
    """Verify the email address and activate the registered account."""
    if request.method == 'GET':
        user = get_object_or_404(User, pk=user_id)

        if not check_email_verification_token(user, token):
            return HttpResponse(
                'Verification link is wrong or has expired.',
                status=HTTPStatus.BAD_REQUEST,
            )
        return render(request, 'accounts/verify_email.html')

    if request.method == 'POST':
        with transaction.atomic():
            user = get_object_or_404(
                User.objects.select_for_update(), pk=user_id
            )

            if not check_email_verification_token(user, token):
                return HttpResponse(
                    'Verification link is wrong or has expired.',
                    status=HTTPStatus.BAD_REQUEST,
                )

            user.is_email_verified = True
            user.is_active = True
            user.save(
                update_fields=[
                    'is_email_verified',
                    'is_active',
                    'modified_at',
                ],
            )

        if request.session.get('pending_verification_user_id') == user.pk:
            request.session.pop('pending_verification_user_id', None)
        return redirect('login')

    return HttpResponseNotAllowed(['GET', 'POST'])


def resend_verification_email(request: HttpRequest) -> HttpResponse:
    """Resend verification email for the pending account."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    user_id = request.session.get('pending_verification_user_id')

    if user_id is not None:
        with transaction.atomic():
            user = User.objects.filter(pk=user_id).select_for_update().first()

            if (
                user is not None
                and not user.is_active
                and not user.is_email_verified
            ):
                now = timezone.now()
                last_attempt = user.verification_email_last_attempt_at

                if last_attempt is None or (now - last_attempt) >= timedelta(
                    seconds=VERIFICATION_EMAIL_RESEND_INTERVAL
                ):
                    token = create_email_verification_token(user)
                    verification_path = reverse(
                        'verify_email',
                        kwargs={
                            'user_id': user_id,
                            'token': token,
                        },
                    )
                    verification_url = (
                        f'{settings.SITE_BASE_URL}{verification_path}'
                    )
                    user.verification_email_last_attempt_at = now
                    user.save(
                        update_fields=[
                            'modified_at',
                            'verification_email_last_attempt_at',
                        ]
                    )
                    transaction.on_commit(
                        partial(
                            send_verification_email_by_celery.delay,
                            to_email=user.email,
                            verification_url=verification_url,
                        ),
                        robust=True,
                    )

    return render(
        request,
        'accounts/verification_pending.html',
        {
            'resend_message': (
                'If your account is awaiting verification and the '
                'resend interval has passed, we will attempt to send '
                'a confirmation email. Check your inbox and spam folder.'
            ),
        },
    )
