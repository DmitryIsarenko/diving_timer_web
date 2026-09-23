from django.urls import path

from .views import (
    exercise_statistics,
    four_step_breathing_exercise,
    index,
    start_four_step_breathing_exercise,
    trainings,
)


urlpatterns = [
    path('', index, name='index'),
    path(
        'exercise-statistics/',
        exercise_statistics,
        name='exercise_statistics',
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
