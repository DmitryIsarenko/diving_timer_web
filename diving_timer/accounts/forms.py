from django import forms
from django.contrib.auth import get_user_model

from .models import User as UserModel


User = get_user_model()


class RegistrationForm(forms.ModelForm):
    """Form for creating a user account."""

    email = forms.CharField(
        label='Email',
        widget=forms.EmailInput,
        required=True,
        help_text='Enter a valid email address.',
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Don`t use weak passwords!',
        required=True,
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput,
        required=True,
    )

    class Meta:
        """Meta class."""

        model = User
        fields = ('email',)

    def clean_email(self) -> str:
        """Normalize the email adress."""
        email: str = self.cleaned_data['email']
        return email.strip().lower()

    def clean(self) -> dict | None:
        """Check that passwords are equal."""
        cleaned_data = super().clean()

        if cleaned_data is None:
            return None

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit: bool = True) -> UserModel:
        """Create a user with hashed password."""
        user: UserModel = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_email_verified = False

        if commit:
            user.save()
        return user
