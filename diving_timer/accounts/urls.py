from django.contrib.auth import views as auth_views
from django.urls import path

from .views import register, resend_verification_email, verify_email


urlpatterns = [
    path('register/', register, name='register'),
    path(
        'verify-email/<int:user_id>/<str:token>/',
        verify_email,
        name='verify_email',
    ),
    path(
        'resend-verification/',
        resend_verification_email,
        name='resend_verification_email',
    ),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
