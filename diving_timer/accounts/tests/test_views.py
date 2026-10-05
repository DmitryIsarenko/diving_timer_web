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


class LogoutViewsTests(TestCase):
    """Class."""
