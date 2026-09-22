from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Вьюха на index страницу."""
    return render(request, 'training/index.html')


def exercise(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise страницу."""
    return render(request, 'training/exercise.html')


@login_required
def exercise_statistics(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise_statistics страницу."""
    return render(request, 'training/exercise_statistics.html')
