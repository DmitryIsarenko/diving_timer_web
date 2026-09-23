from django.urls import path

from .views import (
    four_step_breathing_exercise,
    index,
    start_four_step_breathing_exercise,
    statistics_trainings,
    statistics_trainings_by_exercise,
    statistics_trainings_by_training,
    trainings,
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
]
