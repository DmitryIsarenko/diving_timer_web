from django.contrib.auth import SESSION_KEY
from django.test import TestCase
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import User


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

    def test_post_creates_user(self) -> None:
        """Post with valid data creates user."""
        users_count_before = User.objects.count()

        email = 'example@mail.com'
        response = self.client.post(
            reverse('register'),
            data={
                'email': email,
                'password1': 'password',
                'password2': 'password',
            },
        )

        users_count_after = User.objects.count()

        self.assertEqual(users_count_before + 1, users_count_after)

        user = User.objects.get(email=email)
        self.assertIsNotNone(user.pk)

        self.assertRedirects(response, reverse('login'))

        self.assertNotIn(SESSION_KEY, self.client.session)

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
