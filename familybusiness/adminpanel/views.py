import csv
import re

from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from django.utils.timezone import now

from adminpanel.forms import UserCreationForm, UserEditForm
from adminpanel.models import Event
from wallet.forms import WalletForm, CategoryForm
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
        'users_with_events': Account.objects.filter(events__isnull=False).distinct().order_by('email'),
        'event_type_mapping': event_type_mapping,
        'current_search': search_query,
        'current_type': event_type,
        'current_user': user_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'now': now(),
    }

    return render(request, 'adminpanel/history_list.html', context)


@login_required
def user_management(request):
    """
    Vue principale pour la gestion des utilisateurs
    """
    # Récupérer tous les utilisateurs
    users = Account.objects.all().order_by('-date_joined')

    # Filtres
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    # Application des filtres
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if role_filter:
        if role_filter == 'admin':
            users = users.filter(is_staff=True)
        elif role_filter == 'user':
            users = users.filter(is_staff=False)
        else:
            users = users.filter(role=role_filter)

    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Statistiques
    total_users = Account.objects.count()
    active_users = Account.objects.filter(is_active=True).count()
    admin_users = Account.objects.filter(is_staff=True).count()
    filtered_count = users.count()

    # Ajouter des informations sur les portefeuilles pour chaque utilisateur
    users_with_stats = []
    for user in users:
        users_with_stats.append({
            'user': user,
            'last_activity': Event.objects.filter(user=user).order_by('-date').first().date if Event.objects.filter(user=user).exists() else None
        })

    # Pagination
    paginator = Paginator(users_with_stats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Rôles disponibles
    available_roles = Account.objects.values_list('role', flat=True).distinct().exclude(role='')

    context = {
        'page_obj': page_obj,
        'users_with_stats': page_obj.object_list,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'filtered_count': filtered_count,
        'available_roles': available_roles,

        # Filtres actuels
        'current_search': search_query,
        'current_role': role_filter,
        'current_status': status_filter,
    }

    return render(request, 'adminpanel/user_management.html', context)


@login_required
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            Event.objects.create(
                date=now(),
                content=f"Nouvel utilisateur créé : {form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                user=request.user,
                type='ADMIN_ACTION'
            )
            return redirect('adminpanel:user_management')
    else:
        form = UserCreationForm()

    return render(request, 'adminpanel/create_user.html', {
        'form': form,
        'title': "Créer un utilisateur",
    })


@login_required
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(Account, id=user_id)

    if user_to_edit == request.user and user_to_edit.is_staff:
        messages.warning(request, "Vous ne pouvez pas modifier votre propre compte administrateur.")
        return redirect('adminpanel:user_management')

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit, current_user_id=user_id)
        if form.is_valid():
            form.save()
            messages.success(request, f'Utilisateur {user_to_edit.get_full_name()} modifié avec succès !')
            Event.objects.create(
                date=now(),
                content=f"Utilisateur modifié : {user_to_edit.get_full_name()}",
                user=request.user,
                type='ADMIN_ACTION'
            )
            return redirect('adminpanel:user_management')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field} : {error}")
    else:
        form = UserEditForm(instance=user_to_edit, current_user_id=user_id)

    # Récupérer la dernière connexion de l'utilisateur
    if Event.objects.filter(user=user_to_edit, type='LOGIN').exists():
        user_last_login = Event.objects.filter(user=user_to_edit, type='LOGIN').order_by('-date').first().date
    else:
        user_last_login = None


    context = {
        'form': form,
        'user_to_edit': user_to_edit,
        'user_last_login': user_last_login,
    }
    return render(request, 'adminpanel/edit_user.html', context)


@login_required
def delete_user(request, user_id):
    """
    Vue pour supprimer un utilisateur
    """
    user_to_delete = get_object_or_404(Account, id=user_id)

    # Empêcher de supprimer son propre compte
    if user_to_delete == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('adminpanel:user_management')

    # Empêcher de supprimer le dernier admin
    if user_to_delete.is_staff and Account.objects.filter(is_staff=True).count() <= 1:
        messages.error(request, "Impossible de supprimer le dernier administrateur.")
        return redirect('adminpanel:user_management')

    if request.method == 'POST':
        try:
            user_name = user_to_delete.get_full_name()
            user_to_delete.delete()
            messages.success(request, f'Utilisateur {user_name} supprimé avec succès.')
            Event.objects.create(
                date=now(),
                content=f"Utilisateur supprimé : {user_name}",
                user=request.user,
                type='ADMIN_ACTION'
            )
            return redirect('adminpanel:user_management')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')

    # Informations sur l'impact de la suppression
    user_wallets = Wallet.objects.filter(users=user_to_delete)
    user_transactions = Transaction.objects.filter(user=user_to_delete)

    context = {
        'user_to_delete': user_to_delete,
        'impact_info': {
            'wallet_count': user_wallets.count(),
            'transaction_count': user_transactions.count(),
            'shared_wallets': user_wallets.annotate(user_count=Count('users')).filter(user_count__gt=1),
        }
    }

    return render(request, 'adminpanel/delete_user.html', context)


@login_required
def wallet_management(request):
    """
    Vue principale pour la gestion des portefeuilles
    """
    # Récupérer tous les portefeuilles avec leurs statistiques
    wallets = Wallet.objects.select_related('owner').prefetch_related('users', 'transactions').order_by('-id')

    # Filtres
    search_query = request.GET.get('search', '')
    owner_filter = request.GET.get('owner', '')

    # Application des filtres
    if search_query:
        wallets = wallets.filter(
            Q(name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query) |
            Q(owner__email__icontains=search_query)
        )

    if owner_filter:
        wallets = wallets.filter(owner_id=owner_filter)

    # Statistiques globales
    filtered_count = wallets.count()

    # Ajouter des statistiques détaillées pour chaque portefeuille
    wallets_with_stats = []
    for wallet in wallets:
        transactions = wallet.transactions.all()
        user_count = wallet.users.count()
        last_transaction = transactions.order_by('-date').first()

        # Calcul de la progression vers l'objectif
        progress = 0
        if wallet.objective > 0:
            progress = min((wallet.balance / wallet.objective) * 100, 100)

        wallets_with_stats.append({
            'wallet': wallet,
            'user_count': user_count,
            'transaction_count': transactions.count(),
            'last_transaction': last_transaction,
            'progress': progress,
            'is_shared': user_count > 1,
            'is_active': transactions.exists(),
        })

    # Pagination
    paginator = Paginator(wallets_with_stats, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Propriétaires de portefeuilles pour le filtre
    wallet_owners = Account.objects.filter(wallet__isnull=False).distinct().order_by('first_name', 'last_name')

    context = {
        'page_obj': page_obj,
        'wallets_with_stats': page_obj.object_list,
        'filtered_count': filtered_count,
        'wallet_owners': wallet_owners,

        # Filtres actuels
        'current_search': search_query,
        'current_owner': owner_filter,
    }

    return render(request, 'adminpanel/wallet_management.html', context)


@login_required
def delete_wallet(request, wallet_id):
    """
    Vue pour supprimer un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    if request.method == 'POST':
        try:
            wallet_name = wallet.name
            transaction_count = wallet.transactions.count()
            wallet.delete()

            messages.success(request,
                             f'Portefeuille "{wallet_name}" et ses {transaction_count} transaction(s) supprimé(s) avec succès.')
            Event.objects.create(
                date=now(),
                content=f"Portefeuille supprimé : {wallet_name}",
                user=request.user,
                type='ADMIN_ACTION'
            )
            return redirect('adminpanel:wallet_management')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')
            Event.objects.create(
                date=now(),
                content=f"Erreur lors de la suppression du portefeuille {wallet.name}: {str(e)}",
                user=request.user,
                type='ERROR'
            )

    # Informations sur l'impact de la suppression
    transactions = wallet.transactions.all()
    users_affected = wallet.users.all()

    context = {
        'wallet': wallet,
        'impact_info': {
            'transaction_count': transactions.count(),
            'users_affected': users_affected,
            'total_amount': transactions.aggregate(total=Sum('amount'))['total'] or 0,
            'income_count': transactions.filter(is_income=True).count(),
            'expense_count': transactions.filter(is_income=False).count(),
        }
    }

    return render(request, 'adminpanel/delete_wallet.html', context)

@login_required
def export_transactions_csv(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Optionnel : vérifier les permissions (admin uniquement)
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas la permission d'exporter les transactions.")
        Event.objects.create(
            date=now(),
            content=f"Tentative d'export de transactions par {request.user.get_full_name()} pour le portefeuille {wallet.name} sans permission.",
            user=request.user,
            type='ERROR'
        )
        return redirect('adminpanel:wallet_management')

    transactions = Transaction.objects.filter(wallet=wallet).order_by('date')

    response = HttpResponse(content_type='text/csv')
    filename = f"transactions_{wallet.name.replace(' ', '_')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Titre', 'Montant (€)', 'Type', 'Auteur'])

    for transaction in transactions:
        writer.writerow([
            transaction.date.strftime('%d/%m/%Y'),
            transaction.title,
            f"{transaction.amount:.2f}",
            'Revenu' if transaction.is_income else 'Dépense',
            transaction.user.get_full_name() if transaction.user else 'Inconnu'
        ])

    Event.objects.create(
        date=now(),
        content=f"Export des transactions du portefeuille {wallet.name} par {request.user.get_full_name()}",
        user=request.user,
        type='ADMIN_ACTION'
    )

    return response


@login_required
def category_management(request):
    """
    Vue principale pour la gestion des catégories
    """
    # Récupérer toutes les catégories avec leurs statistiques
    categories = Category.objects.annotate(
        transaction_count=Count('transaction'),
        used_by_wallets=Count('transaction__wallet', distinct=True)
    ).order_by('name')

    # Filtres
    search_query = request.GET.get('search', '')
    usage_filter = request.GET.get('usage', '')

    # Application des filtres
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    if usage_filter:
        if usage_filter == 'used':
            categories = categories.filter(transaction_count__gt=0)
        elif usage_filter == 'unused':
            categories = categories.filter(transaction_count=0)

    # Statistiques globales
    total_categories = Category.objects.count()
    used_categories = Category.objects.filter(transaction__isnull=False).distinct().count()
    unused_categories = total_categories - used_categories
    filtered_count = categories.count()

    # Ajouter des informations détaillées pour chaque catégorie
    categories_with_stats = []
    for category in categories:
        recent_transactions = Transaction.objects.filter(category=category).order_by('-date')[:3]
        last_used = recent_transactions.first().date if recent_transactions.exists() else None

        categories_with_stats.append({
            'category': category,
            'transaction_count': category.transaction_count,
            'used_by_wallets': category.used_by_wallets,
            'last_used': last_used,
            'recent_transactions': recent_transactions,
        })

    # Pagination
    paginator = Paginator(categories_with_stats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories_with_stats': page_obj.object_list,
        'total_categories': total_categories,
        'used_categories': used_categories,
        'unused_categories': unused_categories,
        'filtered_count': filtered_count,

        # Filtres actuels
        'current_search': search_query,
        'current_usage': usage_filter,
    }

    return render(request, 'adminpanel/category_management.html', context)


@login_required
def create_category(request):
    """
    Vue pour créer une nouvelle catégorie
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['name'].strip()

            # Vérifier si la catégorie existe déjà (insensible à la casse)
            if Category.objects.filter(name__iexact=category_name).exists():
                messages.error(request, f'La catégorie "{category_name}" existe déjà.')
            else:
                category = form.save()
                messages.success(request, f'Catégorie "{category.name}" créée avec succès !')
                Event.objects.create(
                    date=now(),
                    content=f"Nouvelle catégorie créée : {category.name}",
                    user=request.user,
                    type='ADMIN_ACTION'
                )
                return redirect('adminpanel:category_management')
        else:
            messages.error(request, 'Veuillez corriger les erreurs du formulaire.')
    else:
        form = CategoryForm()

    context = {
        'form': form,
    }

    return render(request, 'adminpanel/create_category.html', context)


@login_required
def edit_category(request, category_id):
    """
    Vue pour modifier une catégorie
    """
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category_name = form.cleaned_data['name'].strip()

            # Vérifier si une autre catégorie a déjà ce nom
            existing_category = Category.objects.filter(name__iexact=category_name).exclude(id=category.id).first()
            if existing_category:
                messages.error(request, f'La catégorie "{category_name}" existe déjà.')
            else:
                old_name = category.name
                category = form.save()
                messages.success(request, f'Catégorie modifiée : "{old_name}" → "{category.name}"')
                Event.objects.create(
                    date=now(),
                    content=f"Catégorie modifiée : {old_name} → {category.name}",
                    user=request.user,
                    type='ADMIN_ACTION'
                )
                return redirect('adminpanel:category_management')
        else:
            messages.error(request, 'Veuillez corriger les erreurs du formulaire.')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
    }

    return render(request, 'adminpanel/edit_category.html', context)


@login_required
def delete_category(request, category_id):
    """
    Vue pour supprimer une catégorie
    """
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete':
            try:
                category_name = category.name
                transaction_count = Transaction.objects.filter(category=category).count()
                category.delete()

                messages.success(request,
                                 f'Catégorie "{category_name}" et ses {transaction_count} transaction(s) supprimée(s) avec succès.')
                Event.objects.create(
                    date=now(),
                    content=f"Catégorie supprimée : {category_name}",
                    user=request.user,
                    type='ADMIN_ACTION'
                )
                return redirect('adminpanel:category_management')
            except Exception as e:
                messages.error(request, f'Erreur lors de la suppression : {str(e)}')

    # Informations sur l'impact de la suppression
    transactions = Transaction.objects.filter(category=category)
    wallets_affected = transactions.values('wallet').distinct()

    context = {
        'category': category,
        'impact_info': {
            'transaction_count': transactions.count(),
            'wallets_affected': wallets_affected.count(),
            'recent_transactions': transactions.order_by('-date')[:5],
        }
    }

    return render(request, 'adminpanel/delete_category.html', context)