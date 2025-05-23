from django.urls import path
from . import views

app_name = "wallet"

urlpatterns = [
    path('wallets/', views.wallet_list, name='wallet_list'),
    path('wallets/create/', views.wallet_create, name='wallet_create'),
    path('wallets/<int:wallet_id>/edit/', views.wallet_update, name='wallet_update'),
    path('wallets/<int:wallet_id>/delete/', views.wallet_delete, name='wallet_delete'),
    path('wallets/<int:wallet_id>/', views.wallet_detail, name='wallet_detail'),
    path('wallets/<int:wallet_id>/add-transaction/', views.add_transaction, name='add_transaction'),
    path('wallets/<int:wallet_id>/transactions/', views.transaction_list, name='transaction_list'),
    path('wallets/<int:wallet_id>/transaction/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),
    path('wallets/<int:wallet_id>/transaction/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    path('wallets/<int:wallet_id>/edit-objective/', views.edit_objective, name='edit_objective'),
    path('wallets/<int:wallet_id>/add-member/', views.add_member, name='add_member'),
    path('<int:wallet_id>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),

]
