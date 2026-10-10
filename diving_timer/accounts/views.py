from functools import partial

from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render

from .email import send_welcome_email
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
                partial(send_welcome_email, to_email=user.email)
            )
            return redirect('login')
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    return HttpResponseNotAllowed(['GET', 'POST'])
