from django.urls import path

from .views import (
    cancel_training_from_training_details,
    cancel_training_from_trainings_by_exercise,
    delete_training,
    four_step_breathing_exercise,
    index,
    start_four_step_breathing_exercise,
    statistics_trainings,
    statistics_trainings_by_exercise,
    statistics_trainings_by_training,
    trainings,
    update_training_status,
)


urlpatterns = [
    path('', index, name='index'),
    path(
        'exercise-statistics/',
        statistics_trainings,
        name='exercise_statistics',
    ),
    path(
        'exercise-statistics/trainings/<int:training_id>/',
        statistics_trainings_by_training,
        name='exercise_statistics_by_training',
    ),
    path(
        'exercise-statistics/<str:exercise_type>/',
        statistics_trainings_by_exercise,
        name='exercise_statistics_by_exercise',
    ),
    path(
        'trainings/',
        trainings,
        name='trainings',
    ),
    path(
        'trainings/four_step_breathing/',
        four_step_breathing_exercise,
        name='four_step_breathing',
    ),
    path(
        'trainings/four_step_breathing/start/',
        start_four_step_breathing_exercise,
        name='start_four_step_breathing_exercise',
    ),
    path(
        'trainings/<int:training_id>/status/',
        update_training_status,
        name='update_training_status',
    ),
    path(
        'trainings/<int:training_id>/delete/',
        delete_training,
        name='delete_training',
    ),
    path(
        'exercise-statistics/<str:exercise_type>/<int:training_id>/cancel/',
        cancel_training_from_trainings_by_exercise,
        name='cancel_training_from_trainings_by_exercise',
    ),
    path(
        'exercise-statistics/trainings/<int:training_id>/cancel/',
        cancel_training_from_training_details,
        name='cancel_training_from_training_details',
    ),
]
