from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_panel, name='admin_panel'),
    path('history/', views.history_list, name='history_list'),
]