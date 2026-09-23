from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def index(request: HttpRequest) -> HttpResponse:
    """Вьюха на index страницу."""
    return render(request, 'training/index.html')


def trainings(request: HttpRequest) -> HttpResponse:
    """Вьюха на trainings страницу."""
    return render(request, 'training/trainings.html')


def four_step_breathing_exercise(request: HttpRequest) -> HttpResponse:
    """View for a four-step-exercise."""
    return render(request, 'training/four_step_breathing.html')


def start_four_step_breathing_exercise(request: HttpRequest) -> HttpResponse:
    """View for starting an exercise as an authorized user."""
    return redirect('training')


@login_required
def exercise_statistics(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise_statistics страницу."""
    return render(request, 'training/exercise_statistics.html')
