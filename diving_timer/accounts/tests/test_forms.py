from django.test import TestCase

from accounts.constants import MAX_EMAIL_LEN
from accounts.forms import RegistrationForm
from accounts.models import User


class TestAccountForms(TestCase):
    """Class for testing forms in account app."""

    def test_valid_data_accepted(self) -> None:
        """Test for accepting valid data inputs."""
        email = 'valid@email.com'
        password = 'Strong!password999'

        form = RegistrationForm(
            data={
                'email': email,
                'password1': password,
                'password2': password,
            }
        )
        self.assertTrue(
            form.is_valid(),
            form.errors.as_json(),
        )

        expected_fields = [
            ('email', email),
            ('password1', password),
            ('password2', password),
        ]
        for field_name, expected_value in expected_fields:
            with self.subTest(value=field_name, expected_value=expected_value):
                self.assertEqual(
                    form.cleaned_data[field_name],
                    expected_value,
                    f'{field_name} in cleaned data should be same to input.',
                )

    def test_different_passwords_not_accepted(self) -> None:
        """Test for input of two different passwords in form."""
        email = 'valid@email.com'
        password1 = 'Strong!password999'
        password2 = 'another_password'

        form = RegistrationForm(
            data={
                'email': email,
                'password1': password1,
                'password2': password2,
            }
        )

        self.assertFalse(
            form.is_valid(),
            form.errors.as_json(),
        )
        self.assertIn(
            'Passwords do not match.',
            form.non_field_errors(),
        )

    def test_required_fields(self) -> None:
        """Test to check all required fields are filled."""
        email = 'valid@email.com'
        password = 'Strong!password999'

        test_groups = [
            ('', password, password, 'email'),
            (email, '', password, 'password1'),
            (email, password, '', 'password2'),
        ]

        for email_field, pw1, pw2, err_field_name in test_groups:
            with self.subTest(
                email_field=email_field,
                password1=pw1,
                password2=pw2,
            ):
                form = RegistrationForm(
                    data={
                        'email': email_field,
                        'password1': pw1,
                        'password2': pw2,
                    },
                )
                self.assertFalse(form.is_valid(), form.errors.as_json())
                self.assertIn(err_field_name, form.errors)
                self.assertEqual(
                    form.errors.as_data()[err_field_name][0].code,
                    'required',
                )

    def test_incorrect_email(self) -> None:
        """Test of incorrect emails."""
        password = 'password'
        test_groups = [
            '@example.ru',
            'example',
        ]

        for incorrect_email in test_groups:
            with self.subTest(email=incorrect_email):
                form = RegistrationForm(
                    data={
                        'email': incorrect_email,
                        'password1': password,
                        'password2': password,
                    },
                )
                self.assertFalse(form.is_valid(), form.errors.as_json())
                self.assertIn('email', form.errors)
                self.assertEqual(
                    form.errors.as_data()['email'][0].code,
                    'invalid',
                )

    def test_success_saving(self) -> None:
        """Test of correct saving."""
        email = 'example@mail.com'
        password = 'password'

        users_count_before = User.objects.count()

        form = RegistrationForm(
            data={
                'email': email,
                'password1': password,
                'password2': password,
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        form.save()

        users_count_after = User.objects.count()

        self.assertEqual(users_count_after, users_count_before + 1)

    def test_creating_new_user_with_same_email(self) -> None:
        """Testing of creating 2nd user with same email."""
        email = 'example@mail.com'
        password = 'password'
        form = RegistrationForm(
            data={
                'email': email,
                'password1': password,
                'password2': password,
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        form.save()

        form = RegistrationForm(
            data={
                'email': email,
                'password1': password,
                'password2': password,
            }
        )
        self.assertFalse(form.is_valid(), form.errors.as_json())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors.as_data()['email'][0].code,
            'unique',
        )
        with self.assertRaises(ValueError):
            form.save()

    def test_email_len_exeeding_limit_not_accepted(self) -> None:
        """Test of too long email."""
        email_ending = '@mail.com'
        email_beginning = 'a' * (MAX_EMAIL_LEN - len(email_ending) + 1)
        email = email_beginning + email_ending

        form = RegistrationForm(
            data={
                'email': email,
                'password1': 'password',
                'password2': 'password',
            },
        )

        self.assertFalse(form.is_valid(), form.errors.as_json())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors.as_data()['email'][0].code,
            'max_length',
        )
