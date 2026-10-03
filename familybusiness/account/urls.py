from django.urls import path
from .views import register_view, login_view, logout_view, request_password_reset, reset_password, profile_view, set_theme

app_name = 'account'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('password-reset/', request_password_reset, name='request_password_reset'),
    path('reset/<uuid:token>/', reset_password, name='reset_password'),

    path('profile/', profile_view, name='profile'),
    path('set-theme/', set_theme, name='set_theme'),
]