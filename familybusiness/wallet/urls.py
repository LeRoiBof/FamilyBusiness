from django.urls import path
from . import views

app_name = "wallet"

urlpatterns = [
    path('wallets/', views.wallet_list, name='wallet_list'),
    path('wallets/create/', views.wallet_create, name='wallet_create'),
    path('wallets/<int:wallet_id>/edit/', views.wallet_update, name='wallet_update'),
    path('wallets/<int:wallet_id>/delete/', views.wallet_delete, name='wallet_delete'),
    path('wallets/<int:wallet_id>/', views.wallet_detail, name='wallet_detail'),

]
