from django.urls import path
from . import views
from adminpanel.views import export_transactions_csv

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
    path('wallets/<int:wallet_id>/export/', export_transactions_csv, name='export_transactions_csv'),

    # Invitations
    path('<int:wallet_id>/generate-invitation/', views.generate_invitation, name='generate_invitation'),
    path('invitation/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('<int:wallet_id>/invitation/<int:invitation_id>/cancel/', views.cancel_invitation, name='cancel_invitation'),

    # Rapports
    path('<int:wallet_id>/rapport/mensuel/', views.generate_monthly_report, name='generate_monthly_report'),
    path('<int:wallet_id>/rapport/trimestriel/', views.generate_quarterly_report, name='generate_quarterly_report'),
    path('<int:wallet_id>/rapport/annuel/', views.generate_annual_report, name='generate_annual_report'),
]
