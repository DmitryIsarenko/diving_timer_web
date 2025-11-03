from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'timer/index.html')


def exercise_prep(request: HttpRequest) -> HttpResponse:
    return render(request, 'timer/exercise_prep.html')


def exercise(request: HttpRequest) -> HttpResponse:
    return render(request, 'timer/exercise.html')


def exercise_statistics(request: HttpRequest) -> HttpResponse:
    return render(request, 'timer/exercise_statistics.html')


