from django.test import Client
import pytest

from accounts.models import User


@pytest.fixture
def user(django_user_model: type[User], db: None) -> User:
    """Create an active user for authenticated scenarios."""
    return django_user_model.objects.create_user(
        email='test_user@mail.com',
        is_active=True,
    )


@pytest.fixture
def other_user(django_user_model: type[User], db: None) -> User:
    """Create another active user for ownership checks."""
    return django_user_model.objects.create_user(
        email='other_test_user@mail.com',
        is_active=True,
    )


@pytest.fixture
def user_client(client: Client, user: User) -> Client:
    """Return a client authenticated as the primary user."""
    client.force_login(user)
    return client


@pytest.fixture
def other_user_client(other_user: User) -> Client:
    """Return a separate client authenticated as another user."""
    other_client = Client()
    other_client.force_login(other_user)
    return other_client

