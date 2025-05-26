from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_panel, name='admin_panel'),
    path('history/', views.history_list, name='history_list'),
    # Gestion des utilisateurs
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    # Gestion des portefeuilles
    path('wallets/', views.wallet_management, name='wallet_management'),
    path('wallets/<int:wallet_id>/delete/', views.delete_wallet, name='delete_wallet'),
    path('wallets/<int:wallet_id>/export/', views.export_transactions_csv, name='export_transactions_csv'),

    # Gestion des catégories
    path('categories/', views.category_management, name='category_management'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
]