from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import FourStepBreathingExerciseStartForm
from .models import FourStepBreathingExercise, Training


def index(request: HttpRequest) -> HttpResponse:
    """Вьюха на index страницу."""
    return render(request, 'training/index.html')


def trainings(request: HttpRequest) -> HttpResponse:
    """Вьюха на trainings страницу."""
    return render(request, 'training/trainings.html')


def four_step_breathing_exercise(request: HttpRequest) -> HttpResponse:
    """View for a four-step-exercise."""
    return render(request, 'training/four_step_breathing.html')


@login_required
@require_POST
def start_four_step_breathing_exercise(request: HttpRequest) -> JsonResponse:
    """View for starting an exercise as an authorized user."""
    form = FourStepBreathingExerciseStartForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {'errors': form.errors.get_json_data()},
            status=400,
        )

    with transaction.atomic():
        exercise = FourStepBreathingExercise.objects.create(
            **form.cleaned_data
        )
        training = Training.objects.create(
            user=request.user,
            exercise=exercise,
            status='in_progress',
        )

    return JsonResponse(
        {
            'training_id': training.pk,
            'status': training.status,
        },
        status=201,
    )


@login_required
def exercise_statistics(request: HttpRequest) -> HttpResponse:
    """Вьюха на exercise_statistics страницу."""
    return render(request, 'training/exercise_statistics.html')
