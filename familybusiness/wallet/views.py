import json
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.utils import timezone

from account.models import Account
from .forms import WalletForm, TransactionForm
from .models import Wallet, Transaction, Category
from adminpanel.models import Event


@login_required(login_url='account:login')
def wallet_list(request):
    wallets = Wallet.objects.filter(users=request.user)
    return render(request, 'wallet/wallet_list.html', {'wallets': wallets})

@login_required(login_url='account:login')
def wallet_create(request):
    if request.method == 'POST':
        form = WalletForm(request.POST)
        if form.is_valid():
            wallet = form.save(commit=False)
            wallet.owner = request.user
            wallet.save()
            form.save_m2m()
            # Ajoute automatiquement le créateur dans les users
            wallet.users.add(request.user)
            Event.objects.create(
                date=timezone.now(),
                content=f"Nouveau portefeuille créé : {wallet.name}",
                user=request.user,
                type='WALLET_CREATE'
            )
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm()
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': 'Créer un Wallet'})

@login_required(login_url='account:login')
def wallet_update(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user != wallet.owner:
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de modification d'un portefeuille non autorisée : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')  # ou 403

    if request.method == 'POST':
        form = WalletForm(request.POST, instance=wallet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Wallet {wallet.name} modifié avec succès !')
            Event.objects.create(
                date=timezone.now(),
                content=f"Portefeuille modifié : {wallet.name}",
                user=request.user,
                type='WALLET_UPDATE'
            )
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm(instance=wallet)
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': 'Modifier le Wallet'})

@login_required(login_url='account:login')
def wallet_delete(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user != wallet.owner:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de suppression d'un portefeuille non autorisée : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        wallet.delete()
        messages.success(request, f'Wallet {wallet.name} supprimé avec succès !')
        Event.objects.create(
            date=timezone.now(),
            content=f"Portefeuille supprimé : {wallet.name}",
            user=request.user,
            type='WALLET_DELETE'
        )
        return redirect('wallet:wallet_list')
    return redirect('wallet:wallet_list')


@login_required(login_url='account:login')
def wallet_detail(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    members = wallet.users.all()
    non_members = Account.objects.exclude(id__in=members.values_list('id', flat=True))

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative d'accès à un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    # Récupérer toutes les transactions du portefeuille
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-date')

    # Transactions récentes (5 dernières)
    recent_transactions = transactions[:5]

    # Calculs pour les indicateurs du mois en cours
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_transactions = transactions.filter(date__gte=start_of_month)
    monthly_income = monthly_transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0

    # Données pour le graphique d'évolution (du 1er du mois jusqu'à aujourd'hui)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
    today = now.date()
    days_in_current_month = (today - start_of_month).days + 1

    daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    # Données de test si pas de transactions
    if not transactions.exists():
        # Générer des données de test
        import random
        for i in range(days_in_current_month):
            date = start_of_month + timedelta(days=i)
            # Simulation de données aléatoires
            daily_data[date]['income'] = random.uniform(0, 150) if random.random() > 0.7 else 0
            daily_data[date]['expense'] = random.uniform(10, 80)
    else:
        # Utiliser les vraies données
        for transaction in transactions.filter(date__gte=start_of_month):
            key = transaction.date.date()
            if transaction.is_income:
                daily_data[key]['income'] += float(transaction.amount)
            else:
                daily_data[key]['expense'] += float(transaction.amount)

    # Préparer les données pour Chart.js
    dates = []
    expenses = []
    incomes = []

    for i in range(days_in_current_month):
        date = start_of_month + timedelta(days=i)
        dates.append(date.strftime('%d/%m'))
        expenses.append(daily_data[date]['expense'])
        incomes.append(daily_data[date]['income'])

    # Données pour le graphique des catégories
    if transactions.exists():
        cat_data = transactions.filter(is_income=False).values(
            'category__name').annotate(total=Sum('amount'))
        category_labels = [c['category__name'] for c in cat_data if c['total']]
        category_values = [float(c['total']) for c in cat_data if c['total']]
    else:
        # Données de test pour les catégories
        category_labels = ['Alimentation', 'Transport', 'Loisirs', 'Shopping', 'Services']
        category_values = [450.50, 120.30, 89.90, 234.60, 78.40]

    # Si pas de données de catégories, utiliser des valeurs par défaut
    if not category_labels:
        category_labels = ['Divers']
        category_values = [0]

    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,

        # Données pour les graphiques (format JSON pour JavaScript)
        'chart_dates': json.dumps(dates),
        'chart_incomes': json.dumps(incomes),
        'chart_expenses': json.dumps(expenses),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),

        'members': members,
        'non_members': non_members,
    }

    return render(request, 'wallet/wallet_detail.html', context)


@login_required
def add_transaction(request, wallet_id):
    """
    Vue pour ajouter une nouvelle transaction à un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative d'ajout d'une transaction à un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.wallet = wallet
            transaction.save()

            # Mettre à jour le solde du portefeuille
            if transaction.is_income:
                wallet.balance += transaction.amount
                messages.success(request, f'Revenu de {transaction.amount}€ ajouté avec succès !')
            else:
                wallet.balance -= transaction.amount
                messages.success(request, f'Dépense de {transaction.amount}€ enregistrée avec succès !')

            wallet.save()
            Event.objects.create(
                date=timezone.now(),
                content=f"Transaction ajoutée ({f"Dépense" if not transaction.is_income else "Revenu"}): {transaction.title} - {transaction.amount}€",
                user=request.user,
                type='TRANSACTION_CREATE'
            )
            return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        form = TransactionForm()
        # Filtrer les catégories pour ne montrer que celles disponibles
        form.fields['category'].queryset = Category.objects.all()

    context = {
        'form': form,
        'wallet': wallet,
    }

    return render(request, 'wallet/add_transaction.html', context)


@login_required
def edit_transaction(request, wallet_id, transaction_id):
    """
    Vue pour modifier une transaction existante
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de modification d'une transaction dans un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    # Sauvegarder les anciennes valeurs pour ajuster le solde
    old_amount = transaction.amount
    old_is_income = transaction.is_income

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # Annuler l'ancienne transaction du solde
            if old_is_income:
                wallet.balance -= old_amount
            else:
                wallet.balance += old_amount

            # Sauvegarder la nouvelle transaction
            transaction = form.save()

            # Appliquer la nouvelle transaction au solde
            if transaction.is_income:
                wallet.balance += transaction.amount
                messages.success(request, 'Revenu modifié avec succès !')
            else:
                wallet.balance -= transaction.amount
                messages.success(request, 'Dépense modifiée avec succès !')

            wallet.save()
            Event.objects.create(
                date=timezone.now(),
                content=f"Transaction modifiée ({f"Dépense" if not transaction.is_income else "Revenu"}): {transaction.title} - {transaction.amount}€",
                user=request.user,
                type='TRANSACTION_UPDATE'
            )
            return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        form = TransactionForm(instance=transaction)
        form.fields['category'].queryset = Category.objects.all()

    context = {
        'form': form,
        'wallet': wallet,
        'transaction': transaction,
        'is_edit': True,
    }

    return render(request, 'wallet/add_transaction.html', context)


@login_required
def delete_transaction(request, wallet_id, transaction_id):
    """
    Vue pour supprimer une transaction
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de suppression d'une transaction dans un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        # Ajuster le solde du portefeuille
        if transaction.is_income:
            wallet.balance -= transaction.amount
            messages.success(request, f'Revenu de {transaction.amount}€ supprimé.')
        else:
            wallet.balance += transaction.amount
            messages.success(request, f'Dépense de {transaction.amount}€ supprimée.')

        wallet.save()
        transaction.delete()

        Event.objects.create(
            date=timezone.now(),
            content=f"Transaction supprimée ({f"Dépense" if not transaction.is_income else "Revenu"}): {transaction.title} - {transaction.amount}€",
            user=request.user,
            type='TRANSACTION_DELETE'
        )
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)

    context = {
        'wallet': wallet,
        'transaction': transaction,
    }

    return render(request, 'wallet/delete_transaction.html', context)


# Vue pour la liste des transactions (bonus)
@login_required
def transaction_list(request, wallet_id):
    """
    Vue pour afficher toutes les transactions d'un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative d'accès à la liste des transactions d'un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    transactions = Transaction.objects.filter(wallet=wallet).order_by('-date')

    # Calculs pour les indicateurs du mois en cours
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_transactions = transactions.filter(date__gte=start_of_month)
    monthly_income = monthly_transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0

    # Filtrage par catégorie si demandé
    category_filter = request.GET.get('category')
    if category_filter:
        transactions = transactions.filter(category_id=category_filter)

    selected_category = get_object_or_404(Category, id=category_filter) if category_filter else None

    # Filtrage par type (revenus/dépenses)
    type_filter = request.GET.get('type')
    if type_filter == 'income':
        transactions = transactions.filter(is_income=True)
    elif type_filter == 'expense':
        transactions = transactions.filter(is_income=False)

    categories = Category.objects.all()

    context = {
        'wallet': wallet,
        'transactions': transactions,
        'categories': categories,
        'current_category': category_filter,
        'selected_category': selected_category,
        'current_type': type_filter,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
    }

    return render(request, 'wallet/transaction_list.html', context)


@login_required
def edit_objective(request, wallet_id):
    """
    Vue pour modifier l'objectif d'un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de modification de l'objectif d'un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        objective = request.POST.get('objective')
        if objective:
            try:
                objective_value = float(objective)
                if objective_value < 0:
                    messages.error(request, 'L\'objectif ne peut pas être négatif.')
                else:
                    old_objective = wallet.objective
                    wallet.objective = objective_value
                    wallet.save()

                    if old_objective != objective_value:
                        messages.success(request,
                                         f'Objectif mis à jour : {objective_value}€ (anciennement {old_objective}€)')
                    else:
                        messages.info(request, 'L\'objectif n\'a pas changé.')

                    Event.objects.create(
                        date=timezone.now(),
                        content=f"Objectif modifié : {wallet.name} - {old_objective}€ à {objective_value}€",
                        user=request.user,
                        type='OBJECTIVE_UPDATE'
                    )
                    return redirect('wallet:wallet_detail', wallet_id=wallet.id)
            except ValueError:
                messages.error(request, 'Veuillez entrer un montant valide.')
        else:
            messages.error(request, 'Veuillez entrer un objectif.')

    # Calculer quelques statistiques utiles
    current_progress = 0
    if wallet.objective > 0:
        current_progress = min((wallet.balance / wallet.objective) * 100, 100)

    # Suggestions d'objectifs basées sur le solde actuel
    suggested_objectives = []
    if wallet.balance > 0:
        suggested_objectives = [
            wallet.balance * Decimal('1.5'),  # 50% de plus
            wallet.balance * Decimal('2'),  # Double
            wallet.balance * Decimal('2.5'),  # 150% de plus
            round((wallet.balance / Decimal('100')) * Decimal('100'), -2) + Decimal('500'),  # Arrondi + 500
        ]
        # Supprimer les doublons et trier
        suggested_objectives = sorted(list(set(suggested_objectives)))

    context = {
        'wallet': wallet,
        'current_progress': current_progress,
        'suggested_objectives': suggested_objectives,
    }

    return render(request, 'wallet/edit_objective.html', context)

@login_required
def add_member(request, wallet_id):
    """
    Vue pour ajouter un membre à un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user != wallet.owner:
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative d'ajout d'un membre à un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(Account, id=user_id)
        wallet.users.add(user)
        messages.success(request, f'{user.get_full_name()} a été ajouté au portefeuille.')
        Event.objects.create(
            date=timezone.now(),
            content=f"Membre ajouté au portefeuille : {user.get_full_name()}",
            user=request.user,
            type='WALLET_UPDATE'
        )
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)

@login_required
def remove_member(request, wallet_id, user_id):
    """
    Vue pour retirer un membre d'un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user != wallet.owner:
        messages.error(request, "Vous n'avez pas accès à ce portefeuille.")
        Event.objects.create(
            date=timezone.now(),
            content=f"Tentative de retrait d'un membre d'un portefeuille non autorisé : {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    user = get_object_or_404(Account, id=user_id)
    if request.user != user:
        wallet.users.remove(user)
        messages.success(request, f'{user.get_full_name()} a été retiré du portefeuille.')
        Event.objects.create(
            date=timezone.now(),
            content=f"Membre retiré du portefeuille : {user.get_full_name()}",
            user=request.user,
            type='WALLET_UPDATE'
        )
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        messages.error(request, "Vous ne pouvez pas vous retirer vous-même du portefeuille.")
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)
