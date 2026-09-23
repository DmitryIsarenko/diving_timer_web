from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import FourStepBreathingExerciseStartForm, TrainingStatusActionForm
from .models import Exercise, FourStepBreathingExercise, Training


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
            exercise_type=Exercise.ExerciseType.FOUR_STEP_BREATHING,
            **form.cleaned_data,
        )
        training = Training.objects.create(
            user=request.user,
            exercise=exercise,
            status=Training.Status.IN_PROGRESS,
        )

    return JsonResponse(
        {
            'training_id': training.pk,
            'status': training.status,
        },
        status=201,
    )


@login_required
def statistics_trainings(request: HttpRequest) -> HttpResponse:
    """Вьюха на statistics_trainings страницу."""
    user = request.user
    trainings = Training.objects.filter(user=user)
    context = {'trainings': trainings}

    total_trainings = Training.objects.filter(user=user)
    trainings_last_30_days = total_trainings.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    completed_trainings = total_trainings.filter(
        status=Training.Status.COMPLETED
    ).count()
    cancelled_trainings = total_trainings.filter(
        status=Training.Status.CANCELLED
    ).count()
    active_trainings = total_trainings.filter(
        status__in=[Training.Status.IN_PROGRESS, Training.Status.PAUSED]
    ).count()

    training_statistics_by_type_raw = (
        trainings.values('exercise__exercise_type')
        .annotate(
            total_trainings=Count('id'),
            completed_trainings=Count(
                'id', filter=Q(status=Training.Status.COMPLETED)
            ),
            cancelled_trainings=Count(
                'id', filter=Q(status=Training.Status.CANCELLED)
            ),
        )
        .order_by('exercise__exercise_type')
    )

    training_statistics_by_type = [
        {
            'exercise_type': statistic['exercise__exercise_type'],
            'name': Exercise.ExerciseType(
                statistic['exercise__exercise_type']
            ).label,
            'total_trainings': statistic['total_trainings'],
            'completed_trainings': statistic['completed_trainings'],
            'cancelled_trainings': statistic['cancelled_trainings'],
        }
        for statistic in training_statistics_by_type_raw
    ]

    context = {
        'total_trainings': total_trainings.count(),
        'trainings_last_30_days': trainings_last_30_days,
        'completed_trainings': completed_trainings,
        'cancelled_trainings': cancelled_trainings,
        'active_trainings': active_trainings,
        'training_statistics_by_type': training_statistics_by_type,
    }

    return render(request, 'training/statistics_trainings.html', context)


@login_required
def statistics_trainings_by_exercise(
    request: HttpRequest,
    exercise_type: str,
) -> HttpResponse:
    """View to show trainings of a certain exercise type."""
    user = request.user
    trainings = Training.objects.filter(
        user=user,
        exercise__exercise_type=exercise_type,
    ).order_by('-created_at')

    context = {
        'exercise_type': exercise_type,
        'exercise_name': 'Циклическая четырёхфазная тренировка',
        'total_trainings': trainings.count(),
        'completed_trainings': trainings.filter(
            status='completed',
        ).count(),
        'cancelled_trainings': trainings.filter(
            status='cancelled',
        ).count(),
        'trainings': trainings,
    }

    return render(request, 'training/statistics_by_exercise.html', context)


@login_required
def statistics_trainings_by_training(
    request: HttpRequest,
    training_id: int,
) -> HttpResponse:
    """View to show trainings of a certain training session."""
    user = request.user
    training = get_object_or_404(Training, user=user, pk=training_id)
    status_label = training.status
    exercise_type = training.exercise.exercise_type
    detail_template = 'training/training_details/four_step_breathing.html'

    match exercise_type:
        case Exercise.ExerciseType.FOUR_STEP_BREATHING:
            exercise: FourStepBreathingExercise = (
                training.exercise.fourstepbreathingexercise
            )

            duration_per_round = (
                exercise.inhale_duration_seconds
                + exercise.inhale_hold_duration_seconds
                + exercise.exhale_duration_seconds
                + exercise.exhale_hold_duration_seconds
            )
            planned_duration = duration_per_round * exercise.round_count

        case _:
            raise Http404('Unsupported exercise type.')
    context = {
        'training': training,
        'exercise': exercise,
        'exercise_type': exercise_type,
        'exercise_name': training.exercise.get_exercise_type_display(),
        'planned_duration': planned_duration,
        'detail_template': detail_template,
    }
    return render(request, 'training/statistics_by_training.html', context)


@login_required
@require_POST
def update_training_status(
    request: HttpRequest,
    training_id: int,
) -> JsonResponse:
    """View for switching exercise statuses."""
    form = TrainingStatusActionForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {'errors': form.errors.get_json_data()},
            status=400,
        )

    with transaction.atomic():
        training = get_object_or_404(
            Training.objects.select_for_update(),
            pk=training_id,
            user=request.user,
        )

        if form.cleaned_data['action'] == 'pause':
            if training.status != Training.Status.IN_PROGRESS:
                return JsonResponse(
                    {'error': 'Only an active training can be paused.'},
                    status=409,
                )
            training.status = Training.Status.PAUSED

            if training.first_paused_at is None:
                training.first_paused_at = timezone.now()
            training.save(update_fields=['status', 'first_paused_at'])

        elif form.cleaned_data['action'] == 'resume':
            if training.status != Training.Status.PAUSED:
                return JsonResponse(
                    {'error': 'Only a paused training can be resumed.'},
                    status=409,
                )
            training.status = Training.Status.IN_PROGRESS
            training.save(update_fields=['status'])

        elif form.cleaned_data['action'] == 'complete':
            if training.status != Training.Status.IN_PROGRESS:
                return JsonResponse(
                    {'error': 'Only an active training can be completed.'},
                    status=409,
                )
            training.status = Training.Status.COMPLETED
            training.completed_at = timezone.now()
            training.save(update_fields=['status', 'completed_at'])

        elif form.cleaned_data['action'] == 'cancel':
            if training.status not in [
                Training.Status.IN_PROGRESS,
                Training.Status.PAUSED,
            ]:
                return JsonResponse(
                    {
                        'error': (
                            'Only an active or paused '
                            'training can be cancelled.'
                        )
                    },
                    status=409,
                )
            training.status = Training.Status.CANCELLED
            training.cancelled_at = timezone.now()
            training.save(update_fields=['status', 'cancelled_at'])
    return JsonResponse(
        {
            'training_id': training.pk,
            'status': training.status,
        }
    )
