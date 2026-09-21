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
            form.save()
            return redirect('login')
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

    return HttpResponseNotAllowed(['GET', 'POST'])
