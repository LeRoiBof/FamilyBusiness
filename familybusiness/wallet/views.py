import json
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.utils import timezone

from .forms import WalletForm
from .models import Wallet, Transaction


@login_required
def wallet_list(request):
    wallets = Wallet.objects.filter(users=request.user)
    return render(request, 'wallet/wallet_list.html', {'wallets': wallets})

@login_required
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
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm()
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': 'Créer un Wallet'})

@login_required
def wallet_update(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user not in wallet.users.all():
        return redirect('wallet:wallet_list')  # ou 403

    if request.method == 'POST':
        form = WalletForm(request.POST, instance=wallet)
        if form.is_valid():
            form.save()
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm(instance=wallet)
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': 'Modifier le Wallet'})

@login_required
def wallet_delete(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user != wallet.owner:
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        wallet.delete()
        return redirect('wallet:wallet_list')
    return redirect('wallet:wallet_list')


@login_required
def wallet_detail(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
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
    }

    return render(request, 'wallet/wallet_detail.html', context)
