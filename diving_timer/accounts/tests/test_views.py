from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone

from accounts.forms import RegistrationForm
from accounts.models import User
from accounts.tokens import (
    check_email_verification_token,
    create_email_verification_token,
)


class RegistrationViewsTests(TestCase):
    """Check registration HTTP scenarios."""

    def test_get_returns_registration_form(self) -> None:
        """Display an unbound registration form."""
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

        form = response.context['form']

        self.assertIsInstance(form, RegistrationForm)
        self.assertFalse(form.is_bound)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        SITE_BASE_URL='https://example.com',
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_TASK_STORE_EAGER_RESULT=False,
    )
    def test_post_creates_user(self) -> None:
        """Create a pending account and send a valid verification link."""
        users_count_before = User.objects.count()
        email = 'example@mail.com'

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('register'),
                data={
                    'email': email,
                    'password1': 'password',
                    'password2': 'password',
                },
            )

        self.assertEqual(
            User.objects.count(),
            users_count_before + 1,
        )
        self.assertContains(response, 'Your account has been created.')
        self.assertTemplateUsed(
            response,
            'accounts/verification_pending.html',
        )

        user = User.objects.get(email=email)

        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.check_password('password'))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(
            self.client.session['pending_verification_user_id'],
            user.pk,
        )
        self.assertIsNotNone(user.verification_email_last_attempt_at)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]

        self.assertEqual(message.to, [email])
        self.assertEqual(
            message.subject,
            'Confirm your email for Diving Timer',
        )

        links = [
            line
            for line in message.body.splitlines()
            if line.startswith('https://example.com/')
        ]
        self.assertEqual(len(links), 1)

        verification_url = urlsplit(links[0])
        match = resolve(verification_url.path)

        self.assertEqual(match.url_name, 'verify_email')
        self.assertEqual(match.kwargs['user_id'], user.pk)
        self.assertTrue(
            check_email_verification_token(
                user,
                match.kwargs['token'],
            ),
        )

    def test_post_with_incorrect_passwords_returns_form_with_errors(
        self,
    ) -> None:
        """Post with invalid data returns form with errors."""
        users_count_before = User.objects.count()
        response = self.client.post(
            reverse('register'),
            data={
                'email': 'example@mail.com',
                'password1': 'password1',
                'password2': 'pass',
            },
        )
        users_count_after = User.objects.count()

        self.assertEqual(users_count_before, users_count_after)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

        form: RegistrationForm = response.context['form']

        self.assertIsInstance(form, RegistrationForm)
        self.assertTrue(form.is_bound)
        self.assertIn('Passwords do not match.', form.errors.as_text())

    def test_only_get_post_allowed(self) -> None:
        """Only GET and POST are allowed."""
        users_count_before = User.objects.count()
        response = self.client.put(
            reverse('register'),
            data={
                'email': 'example@mail.com',
                'password1': 'password',
                'password2': 'password',
            },
        )
        users_count_after = User.objects.count()

        self.assertEqual(response.status_code, 405)
        self.assertEqual(users_count_before, users_count_after)

        allowed_methods = {
            method.strip() for method in response.headers['Allow'].split(',')
        }

        self.assertEqual(allowed_methods, {'GET', 'POST'})


class LoginViewsTests(TestCase):
    """Check login HTTP scenarios."""

    def test_get_returns_login_form(self) -> None:
        """GET retuns login page with form."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

        self.assertIsNotNone(response.context['form'])

    def test_post_logins_user(self) -> None:
        """POST with valid data logins user."""
        email = 'example@mail.com'
        password = 'password'
        user = User.objects.create_user(
            email=email,
            password=password,
            is_active=True,
        )
        user.refresh_from_db()

        response = self.client.post(
            reverse('login'),
            data={
                'username': email,
                'password': password,
            },
        )

        self.assertRedirects(response, reverse('index'))
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.session[SESSION_KEY], str(user.pk))

    def test_post_with_invalid_data(self) -> None:
        """POST with invalid data does not authorize user."""
        user_email = 'example@mail.com'
        user_password = 'password'
        User.objects.create_user(
            email=user_email,
            password=user_password,
            is_active=True,
        )

        test_sets = [
            (user_email, 'wrong_password', 'invalid_login'),
            ('wrong@email.com', user_password, 'invalid_login'),
        ]

        for email, password, expected_error_code in test_sets:
            with self.subTest(email=email, password=password):
                response = self.client.post(
                    reverse('login'),
                    data={
                        'username': email,
                        'password': password,
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertNotIn(SESSION_KEY, self.client.session)
                form = response.context['form']
                error_codes = {
                    error.code for error in form.non_field_errors().as_data()
                }
                self.assertIn(expected_error_code, error_codes)

    def test_inactive_user_cannot_login(self) -> None:
        """Inactive user cannot login."""
        email = 'example@mail.com'
        password = 'password'
        user = User.objects.create_user(
            email=email,
            password=password,
            is_active=False,
        )
        user.refresh_from_db()

        response = self.client.post(
            reverse('login'),
            data={
                'username': email,
                'password': password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)


class LogoutViewsTests(TestCase):
    """Check logout HTTP scenarios."""

    def setUp(self) -> None:
        """Setting up data."""
        super().setUp()
        user_email = 'example@mail.com'
        user_password = 'password'
        self.user = User.objects.create_user(
            email=user_email,
            password=user_password,
            is_active=True,
        )

        self.client.force_login(self.user)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))

    def test_post_performs_logout(self) -> None:
        """POST forces logout and redirect to index."""
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('index'))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_get_do_not_logout(self) -> None:
        """GET does not log user out."""
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))


class EmailVerificationViewsTests(TestCase):
    """Check email verification HTTP scenarios."""

    def setUp(self) -> None:
        """Create an inactive user and a verification URL."""
        self.user = User.objects.create_user(
            email='verify@example.com',
            password='test-password',
            is_active=False,
            is_email_verified=False,
        )
        self.token = create_email_verification_token(self.user)
        self.url = reverse(
            'verify_email',
            kwargs={
                'user_id': self.user.pk,
                'token': self.token,
            },
        )

    def test_get_does_not_activate_user(self) -> None:
        """Display confirmation without changing user state."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'accounts/verify_email.html',
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_post_activates_user(self) -> None:
        """Activate the account and clear its pending session entry."""
        session = self.client.session
        session['pending_verification_user_id'] = self.user.pk
        session.save()

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('login'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn(
            'pending_verification_user_id',
            self.client.session,
        )

    def test_invalid_token_does_not_activate_user(self) -> None:
        """Reject an invalid token for GET and POST."""
        invalid_url = reverse(
            'verify_email',
            kwargs={
                'user_id': self.user.pk,
                'token': f'x{self.token}',
            },
        )

        for method in ('get', 'post'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(invalid_url)

                self.assertEqual(response.status_code, 400)
                self.user.refresh_from_db()
                self.assertFalse(self.user.is_active)
                self.assertFalse(self.user.is_email_verified)

    def test_used_token_does_not_reactivate_user(self) -> None:
        """Reject a used token after the account is deactivated."""
        self.client.post(self.url)

        self.user.refresh_from_db()
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)

    def test_post_without_csrf_does_not_activate_user(self) -> None:
        """Reject confirmation without a CSRF token."""
        client = Client(enforce_csrf_checks=True)
        client.get(self.url)

        response = client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_post_with_csrf_activates_user(self) -> None:
        """Accept confirmation with a valid CSRF token."""
        client = Client(enforce_csrf_checks=True)
        get_response = client.get(self.url)

        self.assertEqual(get_response.status_code, 200)

        csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(
            self.url,
            data={'csrfmiddlewaretoken': csrf_token},
        )

        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)

    def test_post_preserves_other_pending_account(self) -> None:
        """Keep the pending session entry for a different account."""
        other_user = User.objects.create_user(
            email='other-pending@example.com',
            password='test-password',
            is_active=False,
            is_email_verified=False,
        )
        session = self.client.session
        session['pending_verification_user_id'] = other_user.pk
        session.save()

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('login'))
        self.assertEqual(
            self.client.session['pending_verification_user_id'],
            other_user.pk,
        )

        self.user.refresh_from_db()
        other_user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertFalse(other_user.is_email_verified)
        self.assertFalse(other_user.is_active)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_BASE_URL='https://example.com',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_TASK_STORE_EAGER_RESULT=False,
)
class ResendVerificationViewsTests(TestCase):
    """Check verification email resend scenarios."""

    def setUp(self) -> None:
        """Create a pending account and bind it to the session."""
        super().setUp()
        self.user = User.objects.create_user(
            email='resend@example.com',
            password='test-password',
            is_active=False,
            is_email_verified=False,
        )
        self.url = reverse('resend_verification_email')

        session = self.client.session
        session['pending_verification_user_id'] = self.user.pk
        session.save()

    def test_post_sends_valid_link_without_previous_attempt(self) -> None:
        """Send a valid link and record the first attempt."""
        self.assertIsNone(self.user.verification_email_last_attempt_at)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'accounts/verification_pending.html',
        )
        self.assertContains(response, response.context['resend_message'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        links = [
            line
            for line in mail.outbox[0].body.splitlines()
            if line.startswith('https://example.com/')
        ]
        self.assertEqual(len(links), 1)
        match = resolve(urlsplit(links[0]).path)

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.verification_email_last_attempt_at)
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
        self.assertEqual(match.url_name, 'verify_email')
        self.assertEqual(match.kwargs['user_id'], self.user.pk)
        self.assertTrue(
            check_email_verification_token(
                self.user,
                match.kwargs['token'],
            ),
        )

    def test_post_does_not_send_during_cooldown(self) -> None:
        """Skip sending when the previous attempt was recent."""
        last_attempt = timezone.now()
        self.user.verification_email_last_attempt_at = last_attempt
        self.user.save(
            update_fields=['verification_email_last_attempt_at'],
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        self.user.refresh_from_db()
        self.assertEqual(
            self.user.verification_email_last_attempt_at,
            last_attempt,
        )

    def test_post_sends_after_cooldown(self) -> None:
        """Send another email after the cooldown."""
        last_attempt = timezone.now() - timedelta(seconds=61)
        self.user.verification_email_last_attempt_at = last_attempt
        self.user.save(
            update_fields=['verification_email_last_attempt_at'],
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        self.user.refresh_from_db()
        current_attempt = self.user.verification_email_last_attempt_at
        self.assertIsNotNone(current_attempt)
        if current_attempt is not None:
            self.assertGreater(current_attempt, last_attempt)

    def test_post_skips_ineligible_accounts(self) -> None:
        """Skip active or verified accounts."""
        for is_active, is_verified in [
            (True, False),
            (False, True),
            (True, True),
        ]:
            with self.subTest(
                is_active=is_active,
                is_verified=is_verified,
            ):
                self.user.is_active = is_active
                self.user.is_email_verified = is_verified
                self.user.save(
                    update_fields=['is_active', 'is_email_verified'],
                )

                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(mail.outbox), 0)
                self.user.refresh_from_db()
                self.assertIsNone(
                    self.user.verification_email_last_attempt_at,
                )

    def test_post_without_pending_session_does_not_send(self) -> None:
        """Skip sending when no pending account is in the session."""
        session = self.client.session
        session.pop('pending_verification_user_id')
        session.save()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, response.context['resend_message'])

    def test_get_is_not_allowed(self) -> None:
        """Reject GET without sending an email."""
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers['Allow'], 'POST')
        self.assertEqual(len(mail.outbox), 0)

    def test_post_without_csrf_does_not_send(self) -> None:
        """Reject an eligible resend request without a CSRF token."""
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session['pending_verification_user_id'] = self.user.pk
        session.save()

        with self.captureOnCommitCallbacks(execute=True):
            response = client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.verification_email_last_attempt_at)

    def test_post_with_csrf_sends_email(self) -> None:
        """Accept an eligible resend request with a CSRF token."""
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session['pending_verification_user_id'] = self.user.pk
        session.save()

        get_response = client.get(reverse('register'))
        self.assertEqual(get_response.status_code, 200)

        csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value

        with self.captureOnCommitCallbacks(execute=True):
            response = client.post(
                self.url,
                data={'csrfmiddlewaretoken': csrf_token},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.verification_email_last_attempt_at)
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_post_for_deleted_account_does_not_send(self) -> None:
        """Skip sending when the pending account no longer exists."""
        self.user.delete()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, response.context['resend_message'])
