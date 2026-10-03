from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User


class TestAccountsModels(TestCase):
    """Class for testings models in accounts app."""

    def setUp(self) -> None:
        """Setting up method."""
        self.password = 'password'

    def test_create_without_username(self) -> None:
        """Test to check behaviour when saving without username."""
        email = 'example@mail.com'
        user = User.objects.create(
            email=email,
            password=self.password,
        )
        user.save()
        user.refresh_from_db()
        self.assertEqual(
            user.username,
            email,
            'user.username should be equal to email.',
        )

    def test_create_with_username(self) -> None:
        """Test of creating user with different username from email."""
        email = 'example@mail.com'
        username = 'username'
        user = User.objects.create(
            email=email,
            username=username,
            password=self.password,
        )
        user.save()
        user.refresh_from_db()
        self.assertNotEqual(
            user.username,
            user.email,
            'user.username should not be equal to email.',
        )

    def test_create_two_users_with_same_email(self) -> None:
        """Test of creating two users with same emails."""
        email = 'example@mail.com'

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                user1 = User.objects.create(
                    email=email,
                    password=self.password,
                )
                user2 = User.objects.create(
                    email=email,
                    password=self.password,
                )
                user1.save()
                user2.save()
                user1.refresh_from_db()
                user2.refresh_from_db()

    def test_create_two_users_with_same_username(self) -> None:
        """Test of creating two users with same usernames."""
        username = 'non-unique-username'

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                user1 = User.objects.create(
                    email='one_email@mail.com',
                    password=self.password,
                    username=username,
                )
                user2 = User.objects.create(
                    email='two_email@mail.com',
                    password=self.password,
                    username=username,
                )
                user1.save()
                user2.save()
                user1.refresh_from_db()
                user2.refresh_from_db()
