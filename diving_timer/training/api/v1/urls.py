from django.urls import path

from .views import (
    FourStepBreathingTrainingCreateAPIView,
    FourStepBreathingTrainingDetailAPIView,
    FourStepBreathingTrainingListAPIView,
    TrainingDetailAPIView,
    TrainingListAPIView,
)


app_name = 'training_api_v1'

urlpatterns = [
    path(
        'trainings/four-step-breathing/create/',
        FourStepBreathingTrainingCreateAPIView.as_view(),
        name='four-step-breathing-create',
    ),
    path(
        'trainings/four-step-breathing/<int:training_id>/',
        FourStepBreathingTrainingDetailAPIView.as_view(),
        name='four-step-breathing-detail',
    ),
    path(
        'trainings/four-step-breathing/',
        FourStepBreathingTrainingListAPIView.as_view(),
        name='four-step-breathing',
    ),
    path(
        'trainings/<int:training_id>/',
        TrainingDetailAPIView.as_view(),
        name='training-detail',
    ),
    path(
        'trainings/',
        TrainingListAPIView.as_view(),
        name='trainings',
    ),
]
