from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request: HttpRequest) -> HttpResponse:
    """Register a new user."""
    if request.method == 'GET':
        form = RegistrationForm()
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            transaction.on_commit(
                lambda: send_mail(
                    subject='Welcome to Diving Timer',
                    message='Welcome!',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                ),
            )

            return redirect('login')
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    return HttpResponseNotAllowed(['GET', 'POST'])
