from django.urls import path

from .views import TrainingDetailAPIView, TrainingListAPIView


app_name = 'training_api_v1'

urlpatterns = [
    path(
        'trainings/',
        TrainingListAPIView.as_view(),
        name='training-list',
    ),
    path(
        'trainings/<int:training_id>/',
        TrainingDetailAPIView.as_view(),
        name='training-detail',
    ),
]
