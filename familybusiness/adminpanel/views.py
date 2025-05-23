from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from django.utils.timezone import now

from adminpanel.models import Event
from wallet.models import Wallet, Transaction, Category
from account.models import Account


@login_required
def admin_panel(request):
    """
    Vue principale du panel d'administration
    Affiche un tableau de bord
    """
    return render(request, 'adminpanel/admin_panel.html')

@login_required
def history_list(request):
    events = Event.objects.all().order_by('-date').order_by('-id')

    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if search_query:
        events = events.filter(
            Q(content__icontains=search_query) |
            Q(type__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    if event_type:
        events = events.filter(type=event_type)

    if user_filter:
        events = events.filter(user_id=user_filter)

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None

    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            # Correction : supprimer __date car le champ est déjà un DateField
            events = events.filter(date__gte=parsed)

    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            # Correction : supprimer __date car le champ est déjà un DateField
            events = events.filter(date__lte=parsed)

    filtered_events = events.count()

    paginator = Paginator(events, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    event_type_mapping = {
        'LOGIN': {'icon': 'mdi-login', 'color': 'is-success', 'label': 'Connexion'},
        'LOGOUT': {'icon': 'mdi-logout', 'color': 'is-info', 'label': 'Déconnexion'},
        'WALLET_CREATE': {'icon': 'mdi-wallet-plus', 'color': 'is-primary', 'label': 'Création portefeuille'},
        'WALLET_DELETE': {'icon': 'mdi-wallet-remove', 'color': 'is-danger', 'label': 'Suppression portefeuille'},
        'WALLET_UPDATE': {'icon': 'mdi-wallet', 'color': 'is-warning', 'label': 'Modification portefeuille'},
        'TRANSACTION_CREATE': {'icon': 'mdi-cash-plus', 'color': 'is-success', 'label': 'Ajout transaction'},
        'TRANSACTION_DELETE': {'icon': 'mdi-cash-remove', 'color': 'is-warning', 'label': 'Suppression transaction'},
        'TRANSACTION_UPDATE': {'icon': 'mdi-cash', 'color': 'is-info', 'label': 'Modification transaction'},
        'OBJECTIVE_UPDATE': {'icon': 'mdi-target', 'color': 'is-info', 'label': 'Modification objectif'},
        'USER_REGISTER': {'icon': 'mdi-account-plus', 'color': 'is-success', 'label': 'Inscription utilisateur'},
        'PASSWORD_CHANGE': {'icon': 'mdi-key-change', 'color': 'is-warning', 'label': 'Changement mot de passe'},
        'ERROR': {'icon': 'mdi-alert-circle', 'color': 'is-danger', 'label': 'Erreur'},
        'ADMIN_ACTION': {'icon': 'mdi-shield-check', 'color': 'is-warning', 'label': 'Action admin'},
        'OTHER': {'icon': 'mdi-help-circle', 'color': 'is-dark', 'label': 'Autre'},
    }

    context = {
        'page_obj': page_obj,
        'events': page_obj.object_list,
        'filtered_events': filtered_events,
        'available_types': Event.objects.values_list('type', flat=True).distinct().order_by('type'),
        'users_with_events': Account.objects.filter(event__isnull=False).distinct().order_by('email'),
        'event_type_mapping': event_type_mapping,
        'current_search': search_query,
        'current_type': event_type,
        'current_user': user_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'now': now(),
    }

    return render(request, 'adminpanel/history_list.html', context)
