from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Вьюха на index страницу."""
    return render(request, 'timer/index.html')


def exercise(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise страницу."""
    return render(request, 'timer/exercise.html')


def exercise_statistics(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise_statistics страницу."""
    return render(request, 'timer/exercise_statistics.html')
