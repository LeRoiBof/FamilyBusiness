import json
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from account.models import Account
from .forms import WalletForm, TransactionForm, InvitationForm
from .models import Wallet, Transaction, Category, WalletInvitation
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
            # Ajoute automatiquement le créateur dans les users
            wallet.users.add(request.user)
            Event.objects.create(
                date=timezone.now(),
                content=_("new_wallet_created") + f": {wallet.name}",
                user=request.user,
                type='WALLET_CREATE'
            )
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm()
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': _("create_wallet")})

@login_required(login_url='account:login')
def wallet_update(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user != wallet.owner:
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_wallet_modification_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')  # ou 403

    if request.method == 'POST':
        form = WalletForm(request.POST, instance=wallet)
        if form.is_valid():
            form.save()
            messages.success(request, _("wallet_modified_successfully").format(wallet_name=wallet.name))
            Event.objects.create(
                date=timezone.now(),
                content=_("wallet_modified") + f": {wallet.name}",
                user=request.user,
                type='WALLET_UPDATE'
            )
            return redirect('wallet:wallet_list')
    else:
        form = WalletForm(instance=wallet)
    return render(request, 'wallet/wallet_form.html', {'form': form, 'title': _("edit_wallet")})

@login_required(login_url='account:login')
def wallet_delete(request, wallet_id):
    wallet = Wallet.objects.get(id=wallet_id)
    if request.user != wallet.owner:
        messages.error(request, _("not_authorized_to_delete_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_wallet_deletion_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        wallet.delete()
        messages.success(request, _("wallet_deleted_successfully").format(wallet_name=wallet.name))
        Event.objects.create(
            date=timezone.now(),
            content=_("wallet_deleted") + f": {wallet.name}",
            user=request.user,
            type='WALLET_DELETE'
        )
        return redirect('wallet:wallet_list')
    return redirect('wallet:wallet_list')


@login_required(login_url='account:login')
def wallet_detail(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    members = wallet.users.all()

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_wallet_access_attempt") + f": {wallet.name}",
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
    start_of_month_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
    today = now.date()
    days_in_current_month = (today - start_of_month_date).days + 1

    daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    # Utiliser uniquement les vraies données
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
        date = start_of_month_date + timedelta(days=i)
        dates.append(date.strftime('%d/%m'))
        expenses.append(daily_data[date]['expense'])
        incomes.append(daily_data[date]['income'])

    # Données pour le graphique des catégories (uniquement les vraies données)
    cat_data = (
        transactions.filter(is_income=False)
        .values('category')  # group by category ID
        .annotate(total=Sum('amount'))
        .order_by('category')
    )
    categories = {
        c.id: c.name for c in Category.objects.filter(
            id__in=[entry['category'] for entry in cat_data]
        )
    }
    category_labels = [categories[entry['category']] for entry in cat_data]
    category_values = [float(entry['total']) for entry in cat_data]

    # Si pas de données de catégories, listes vides
    if not category_labels:
        category_labels = []
        category_values = []

    # Récupérer les invitations actives pour ce wallet
    active_invitations = WalletInvitation.objects.filter(
        wallet=wallet,
        is_used=False,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')

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
        'active_invitations': active_invitations,
        'invitation_form': InvitationForm(),
    }

    return render(request, 'wallet/wallet_detail.html', context)


@login_required
def generate_invitation(request, wallet_id):
    """
    Vue pour générer un lien d'invitation pour un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur est le propriétaire du portefeuille
    if request.user != wallet.owner:
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_invitation_generation_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            # Créer une nouvelle invitation
            invitation = WalletInvitation.objects.create(
                wallet=wallet,
                created_by=request.user
            )

            # Générer l'URL complète
            invitation_url = request.build_absolute_uri(
                reverse('wallet:accept_invitation', kwargs={'token': invitation.token})
            )

            messages.success(request, _("invitation_generated_successfully"))

            Event.objects.create(
                date=timezone.now(),
                content=_("invitation_generated") + f": {wallet.name}",
                user=request.user,
                type='INVITATION_CREATE'
            )

            return redirect('wallet:wallet_detail', wallet_id=wallet.id)

    return redirect('wallet:wallet_detail', wallet_id=wallet.id)


def accept_invitation(request, token):
    """
    Vue pour accepter une invitation via token
    """
    try:
        invitation = get_object_or_404(WalletInvitation, token=token)
    except:
        messages.error(request, _("invalid_invitation_token"))
        return redirect('account:login')

    # Vérifier si l'invitation est valide
    if not invitation.is_valid():
        if invitation.is_used:
            messages.error(request, _("invitation_already_used"))
        else:
            messages.error(request, _("invitation_expired"))
        return redirect('account:login')

    # Si l'utilisateur n'est pas connecté, rediriger vers la connexion
    if not request.user.is_authenticated:
        # Stocker le token en session pour l'utiliser après connexion
        request.session['invitation_token'] = str(token)
        messages.info(request, _("please_login_to_accept_invitation"))
        return redirect('account:login')

    # Vérifier si l'utilisateur est déjà membre du portefeuille
    if request.user in invitation.wallet.users.all():
        messages.info(request, _("already_member_of_wallet"))
        return redirect('wallet:wallet_detail', wallet_id=invitation.wallet.id)

    # Ajouter l'utilisateur au portefeuille
    invitation.wallet.users.add(request.user)

    # Marquer l'invitation comme utilisée
    invitation.is_used = True
    invitation.used_by = request.user
    invitation.used_at = timezone.now()
    invitation.save()

    messages.success(request, _("successfully_joined_wallet").format(wallet_name=invitation.wallet.name))

    Event.objects.create(
        date=timezone.now(),
        content=_("member_joined_via_invitation") + f": {request.user.get_full_name()} → {invitation.wallet.name}",
        user=request.user,
        type='WALLET_JOIN'
    )

    return redirect('wallet:wallet_detail', wallet_id=invitation.wallet.id)

@login_required
def cancel_invitation(request, wallet_id, invitation_id):
    """
    Vue pour annuler une invitation
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    invitation = get_object_or_404(WalletInvitation, id=invitation_id, wallet=wallet)

    # Vérifier que l'utilisateur est le propriétaire du portefeuille
    if request.user != wallet.owner:
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        invitation.delete()
        messages.success(request, _("invitation_cancelled_successfully"))
        Event.objects.create(
            date=timezone.now(),
            content=_("invitation_cancelled") + f": {wallet.name}",
            user=request.user,
            type='INVITATION_CANCEL'
        )

    return redirect('wallet:wallet_detail', wallet_id=wallet.id)

@login_required
def add_transaction(request, wallet_id):
    """
    Vue pour ajouter une nouvelle transaction à un portefeuille
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Vérifier que l'utilisateur a accès à ce portefeuille
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transaction_addition_attempt") + f": {wallet.name}",
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
                messages.success(request, _("income_added_successfully").format(amount=transaction.amount))
            else:
                wallet.balance -= transaction.amount
                messages.success(request, _("expense_recorded_successfully").format(amount=transaction.amount))

            wallet.save()
            Event.objects.create(
                date=timezone.now(),
                content=_("transaction_added") + f" ({_('expense') if not transaction.is_income else _('income')}): {transaction.title} - {transaction.amount}€",
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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transaction_modification_attempt") + f": {wallet.name}",
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
                messages.success(request, _("income_modified_successfully"))
            else:
                wallet.balance -= transaction.amount
                messages.success(request, _("expense_modified_successfully"))

            wallet.save()
            Event.objects.create(
                date=timezone.now(),
                content=_("transaction_modified") + f" ({_('expense') if not transaction.is_income else _('income')}): {transaction.title} - {transaction.amount}€",
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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transaction_deletion_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        # Ajuster le solde du portefeuille
        if transaction.is_income:
            wallet.balance -= transaction.amount
            messages.success(request, _("income_deleted").format(amount=transaction.amount))
        else:
            wallet.balance += transaction.amount
            messages.success(request, _("expense_deleted").format(amount=transaction.amount))

        wallet.save()
        transaction.delete()

        Event.objects.create(
            date=timezone.now(),
            content=_("transaction_deleted") + f" ({_('expense') if not transaction.is_income else _('income')}): {transaction.title} - {transaction.amount}€",
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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transaction_list_access_attempt") + f": {wallet.name}",
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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_objective_modification_attempt") + f": {wallet.name}",
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
                    messages.error(request, _("objective_cannot_be_negative"))
                else:
                    old_objective = wallet.objective
                    wallet.objective = objective_value
                    wallet.save()

                    if old_objective != objective_value:
                        messages.success(request, _("objective_updated_successfully").format(
                            new_objective=objective_value,
                            old_objective=old_objective
                        ))
                    else:
                        messages.info(request, _("objective_unchanged"))

                    Event.objects.create(
                        date=timezone.now(),
                        content=_("objective_modified") + f": {wallet.name} - {old_objective}€ → {objective_value}€",
                        user=request.user,
                        type='OBJECTIVE_UPDATE'
                    )
                    return redirect('wallet:wallet_detail', wallet_id=wallet.id)
            except ValueError:
                messages.error(request, _("please_enter_valid_amount"))
        else:
            messages.error(request, _("please_enter_objective"))

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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_member_addition_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(Account, id=user_id)
        wallet.users.add(user)
        messages.success(request, _("member_added_to_wallet").format(user_name=user.get_full_name()))
        Event.objects.create(
            date=timezone.now(),
            content=_("member_added_to_wallet_log") + f": {user.get_full_name()}",
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
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_member_removal_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    user = get_object_or_404(Account, id=user_id)
    if request.user != user:
        wallet.users.remove(user)
        messages.success(request, _("member_removed_from_wallet").format(user_name=user.get_full_name()))
        Event.objects.create(
            date=timezone.now(),
            content=_("member_removed_from_wallet_log") + f": {user.get_full_name()}",
            user=request.user,
            type='WALLET_UPDATE'
        )
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        messages.error(request, _("cannot_remove_yourself_from_wallet"))
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)