from django.test import TestCase

from accounts.managers import CustomUserManager
from accounts.models import User


class TestCustomUserManager(TestCase):
    """Test class for testing UserManager."""

    def setUp(self) -> None:
        """Preparing data."""
        self.email = 'TesT_email@TEST.RU'
        self.hard_normalized_email = 'TesT_email@test.ru'
        self.normalized_email = CustomUserManager.normalize_email(self.email)

        self.password = 'password'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
        )

        self.superuser_email = 'test_super_email@test.ru'
        self.superuser_password = 'password'
        self.super_user = User.objects.create_superuser(
            email=self.superuser_email,
            password=self.superuser_password,
        )

    def test_create_user(self) -> None:
        """Test of creating a user."""
        self.assertIsNotNone(self.user.pk, 'PK is None after creation.')
        self.assertEqual(
            self.user.email,
            self.normalized_email,
            'user.email is not simular to test email.',
        )

    def test_fill_username(self) -> None:
        """Test of filling up the username field for created user."""
        self.assertIsNotNone(self.user.username, 'Username was set to None.')
        self.assertEqual(
            self.user.username,
            self.normalized_email,
            'Username is not equal to normalized email.',
        )

    def test_password(self) -> None:
        """Test of hashing a password."""
        self.assertTrue(
            self.user.check_password(self.password),
            'user.check_password check failed.',
        )
        self.assertNotEqual(
            self.password,
            self.user.password,
            'Password is not hashed!',
        )

        self.assertTrue(
            self.super_user.check_password(self.superuser_password),
            'user.check_password check failed.',
        )
        self.assertNotEqual(
            self.superuser_password,
            self.super_user.password,
            'Password is not hashed!',
        )

    def test_flags(self) -> None:
        """Test of flags by default at creating user and superuser."""
        self.assertFalse(
            self.user.is_active,
            'Regular user must not be active',
        )
        self.assertFalse(
            self.user.is_staff,
            'Regular user must not be staff',
        )
        self.assertFalse(
            self.user.is_superuser,
            'Regular user must not be superuser',
        )
        self.assertTrue(
            self.super_user.is_active,
            'Superuser must be active',
        )
        self.assertTrue(
            self.super_user.is_staff,
            'Superuser must be staff',
        )
        self.assertTrue(
            self.super_user.is_superuser,
            'Superuser must be superuser',
        )

    def test_added_flags(self) -> None:
        """Test that adding a flag changes flag."""
        user = User.objects.create_user(
            email='active_user@ex.ru',
            password=self.password,
            is_active=True,
        )
        user.refresh_from_db()

        self.assertTrue(user.is_active)

    def test_email_normalization(self) -> None:
        """Test of normalization of an email."""
        self.assertEqual(
            self.user.email,
            self.hard_normalized_email,
            'Only domain part should be normalized.',
        )
        self.assertEqual(
            self.user.username,
            self.hard_normalized_email,
            'Only domain part should be normalized.',
        )

    def test_create_user_without_email(self) -> None:
        """Testing creation with wrong or without an email."""
        values_results = [
            (None, ValueError),
            ('', ValueError),
        ]

        for value, expected_result in values_results:
            with self.subTest(email=value):
                with self.assertRaises(expected_result):
                    User.objects.create_user(
                        email=value,
                        password=self.password,
                    )

    def test_create_superuser_without_email(self) -> None:
        """Testing creation with wrong or without an email."""
        values_results = [
            (None, ValueError),
            ('', ValueError),
        ]

        for value, expected_result in values_results:
            with self.subTest(email=value):
                with self.assertRaises(expected_result):
                    User.objects.create_superuser(
                        email=value,
                        password=self.password,
                    )

    def test_create_user_without_password(self) -> None:
        """Test of creating users and superusers without a password."""
        regular_user = User.objects.create_user(email='__' + self.email)
        self.assertFalse(regular_user.has_usable_password())

    def test_create_superuser_without_password(self) -> None:
        """Test of creating users and superusers without a password."""
        sup_user = User.objects.create_superuser(
            email='__' + self.superuser_email
        )
        self.assertFalse(sup_user.has_usable_password())

    def test_create_superuser_not_staff(self) -> None:
        """Test of creating superuser but not a staff."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='super@ex.ru',
                password=self.password,
                is_staff=False,
            )

    def test_create_superuser_not_superuser(self) -> None:
        """Test of creating superuser but not a staff."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='super@ex.ru',
                password=self.password,
                is_superuser=False,
            )
