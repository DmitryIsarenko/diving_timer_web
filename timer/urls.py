from django.urls import path
from .views import index, exercise, exercise_statistics


urlpatterns = [
    path('', index, name='index'),
    # path('exercise-prep/', exercise_prep, name='exercise_prep'),
    path('exercise/', exercise, name='exercise'),
    path('exercise-statistics/', exercise_statistics, name='exercise_statistics'),
]


