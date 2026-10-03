import io
import json
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from xhtml2pdf import pisa

from account.models import Account
from .forms import WalletForm, TransactionForm, InvitationForm, FutureTransactionForm, TransferForm
from .models import Wallet, Transaction, Category, WalletInvitation, FutureTransaction

TRANSFER_CATEGORY_NAME = 'Transfert'
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
            # Automatically add the owner to the users
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


def _percent_change(current, previous):
    if not previous:
        return None
    return float((current - previous) / previous * 100)


@login_required(login_url='account:login')
def wallet_detail(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    members = wallet.users.all()

    # Check user has access to wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_wallet_access_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    # Get all wallet trx
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-date')

    # Recent trx
    recent_transactions = transactions[:5]

    # Compute monthly indicators
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_month_date = start_of_month.date()

    monthly_transactions = transactions.filter(date__gte=start_of_month_date)
    monthly_income = monthly_transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0

    # Comparaison avec le mois précédent
    start_of_last_month_date = (start_of_month_date - timedelta(days=1)).replace(day=1)
    last_month_transactions = transactions.filter(date__gte=start_of_last_month_date, date__lt=start_of_month_date)
    last_month_income = last_month_transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    last_month_expenses = last_month_transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0
    income_change_percent = _percent_change(monthly_income, last_month_income)
    expenses_change_percent = _percent_change(monthly_expenses, last_month_expenses)

    future_transactions = FutureTransaction.objects.filter(wallet=wallet, active=True)

    # Échéances dans les prochaines 24h
    upcoming_transactions = future_transactions.filter(
        execution_date__gte=now, execution_date__lte=now + timedelta(hours=24)
    ).order_by('execution_date')

    # data for evolution plot (from 1st of the month to today)
    today = now.date()
    days_in_current_month = (today - start_of_month_date).days + 1

    daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    for transaction in transactions.filter(date__gte=start_of_month_date):
        key = transaction.date
        if transaction.is_income:
            daily_data[key]['income'] += float(transaction.amount)
        else:
            daily_data[key]['expense'] += float(transaction.amount)

    # prepare data for Chart.js
    dates = []
    expenses = []
    incomes = []

    for i in range(days_in_current_month):
        date = start_of_month_date + timedelta(days=i)
        dates.append(date.strftime('%d/%m'))
        expenses.append(daily_data[date]['expense'])
        incomes.append(daily_data[date]['income'])

    # data for category plot
    cat_data = (
        transactions.filter(is_income=False)
        .values('category')  # group by category ID
        .annotate(total=Sum('amount'))
        .order_by('category')
    )
    categories = {
        c.id: c for c in Category.objects.filter(
            id__in=[entry['category'] for entry in cat_data]
        )
    }
    category_labels = [categories[entry['category']].name for entry in cat_data]
    category_values = [float(entry['total']) for entry in cat_data]
    category_colors = [categories[entry['category']].get_color_hex() for entry in cat_data]

    # if not data on categories, empty lists
    if not category_labels:
        category_labels = []
        category_values = []
        category_colors = []

    # Get all active invites for the wallet
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
        'income_change_percent': income_change_percent,
        'expenses_change_percent': expenses_change_percent,

        'upcoming_transactions': upcoming_transactions,

        # plot data (JSON format for JavaScript)
        'chart_dates': json.dumps(dates),
        'chart_incomes': json.dumps(incomes),
        'chart_expenses': json.dumps(expenses),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'category_colors': json.dumps(category_colors),

        'members': members,
        'active_invitations': active_invitations,
        'invitation_form': InvitationForm(),
    }

    return render(request, 'wallet/wallet_detail.html', context)


@login_required
def generate_invitation(request, wallet_id):
    """
    View to generate and invitation link
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user trying to create the invitation is the owner
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
            # Create a new invite
            invitation = WalletInvitation.objects.create(
                wallet=wallet,
                created_by=request.user
            )

            # Generate the invite URL
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

    # If the user is not authenticated store token and redirect to login
    if not request.user.is_authenticated:
        request.session['invitation_token'] = str(token)
        messages.info(request, _("please_login_to_accept_invitation"))
        return redirect('account:login')

    try:
        invitation = get_object_or_404(WalletInvitation, token=token)
    except:
        messages.error(request, _("invalid_invitation_token"))
        return redirect('wallet:wallet_list')

    if not invitation.is_valid():
        if invitation.is_used:
            messages.error(request, _("invitation_already_used"))
        else:
            messages.error(request, _("invitation_expired"))

        return redirect('wallet:wallet_list')

    if request.user in invitation.wallet.users.all():
        messages.error(request, "Already in the wallet")
        messages.info(request, _("already_member_of_wallet"))
        return redirect('wallet:wallet_detail', wallet_id=invitation.wallet.id)

    # If not, add to wallet
    invitation.wallet.users.add(request.user)

    # Mark invitation link as used (Can only be used once)
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
    View to cancel invitation
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    invitation = get_object_or_404(WalletInvitation, id=invitation_id, wallet=wallet)

    # Check that the user trying to cancel the invitation is the owner
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
    View to add a new transaction to the wallet
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the wallet
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

            # Update wallet balance
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
        # Show only available categories
        form.fields['category'].queryset = Category.objects.all()

    context = {
        'form': form,
        'wallet': wallet,
    }

    return render(request, 'wallet/add_transaction.html', context)

@login_required()
def add_future_transaction(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')
    
    if request.method == 'POST':
        form = FutureTransactionForm(request.POST)
        if form.is_valid():
            future_trx = form.save(commit=False)
            future_trx.wallet = wallet
            future_trx.user = request.user
            future_trx.save()
            messages.success(request, _("future_transaction_created"))
            return redirect('wallet:wallet_detail', wallet_id=wallet.id)
        
    else:
        form = FutureTransactionForm()
        
    return render(request, 'wallet/add_future_transaction.html', {'form': form, 'wallet': wallet})

@login_required
def add_transfer(request, wallet_id):
    """
    View to transfer money between two wallets the user is a member/owner of
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the source wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transfer_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    if not Wallet.objects.filter(users=request.user).exclude(pk=wallet.pk).exists():
        messages.error(request, _("no_other_wallet_for_transfer"))
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)

    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user, source_wallet=wallet)
        if form.is_valid():
            destination_wallet = form.cleaned_data['destination_wallet']
            amount = form.cleaned_data['amount']
            date = form.cleaned_data['date']
            description = form.cleaned_data['description']

            # Created on first use if it doesn't already exist
            transfer_category, _created = Category.objects.get_or_create(
                name=TRANSFER_CATEGORY_NAME,
                defaults={'color': 'info', 'icon': 'mdi-bank-transfer'}
            )

            with db_transaction.atomic():
                outgoing = Transaction.objects.create(
                    title=_("transfer_to").format(wallet_name=destination_wallet.name),
                    category=transfer_category,
                    user=request.user,
                    amount=amount,
                    date=date,
                    wallet=wallet,
                    description=description,
                    is_income=False,
                    is_transfer=True,
                )
                incoming = Transaction.objects.create(
                    title=_("transfer_from").format(wallet_name=wallet.name),
                    category=transfer_category,
                    user=request.user,
                    amount=amount,
                    date=date,
                    wallet=destination_wallet,
                    description=description,
                    is_income=True,
                    is_transfer=True,
                )
                outgoing.linked_transaction = incoming
                outgoing.save(update_fields=['linked_transaction'])
                incoming.linked_transaction = outgoing
                incoming.save(update_fields=['linked_transaction'])

                wallet.balance -= amount
                wallet.save()
                destination_wallet.balance += amount
                destination_wallet.save()

            messages.success(request, _("transfer_successful").format(
                amount=amount, destination=destination_wallet.name
            ))
            Event.objects.create(
                date=timezone.now(),
                content=_("transfer_executed") + f": {wallet.name} → {destination_wallet.name} - {amount}€",
                user=request.user,
                type='TRANSACTION_CREATE'
            )
            return redirect('wallet:wallet_detail', wallet_id=wallet.id)
    else:
        form = TransferForm(user=request.user, source_wallet=wallet)

    context = {
        'form': form,
        'wallet': wallet,
    }

    return render(request, 'wallet/add_transfer.html', context)

@login_required
def edit_transaction(request, wallet_id, transaction_id):
    """
    View to edit a wallet's transaction
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)

    # Check that the user is a member of the wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        Event.objects.create(
            date=timezone.now(),
            content=_("unauthorized_transaction_modification_attempt") + f": {wallet.name}",
            user=request.user,
            type='ERROR'
        )
        return redirect('wallet:wallet_list')

    # Transfers are edited as a pair and can't be modified through the regular transaction form
    if transaction.is_transfer:
        messages.error(request, _("cannot_edit_transfer"))
        return redirect('wallet:wallet_detail', wallet_id=wallet.id)

    old_amount = transaction.amount
    old_is_income = transaction.is_income

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # Replace previous transaction
            if old_is_income:
                wallet.balance -= old_amount
            else:
                wallet.balance += old_amount

            # Save new transaction
            transaction = form.save()

            # Update the wallet's balance
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
    View to delete a wallet's transaction
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)

    # Check that the user is a member of the wallet
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
        linked_transaction = transaction.linked_transaction

        with db_transaction.atomic():
            # Update wallet's balance
            if transaction.is_income:
                wallet.balance -= transaction.amount
                messages.success(request, _("income_deleted").format(amount=transaction.amount))
            else:
                wallet.balance += transaction.amount
                messages.success(request, _("expense_deleted").format(amount=transaction.amount))

            wallet.save()
            transaction.delete()

            # Reverse the other leg of the transfer too, so it never ends up one-sided
            if linked_transaction is not None:
                other_wallet = linked_transaction.wallet
                if linked_transaction.is_income:
                    other_wallet.balance -= linked_transaction.amount
                else:
                    other_wallet.balance += linked_transaction.amount
                other_wallet.save()
                linked_transaction.delete()

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


@login_required
def transaction_list(request, wallet_id):
    """
    View to display a list of all wallet's transactions
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the wallet
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

    # Compute wallet's indicators
    now = timezone.now()
    start_of_month_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

    monthly_transactions = transactions.filter(date__gte=start_of_month_date)
    monthly_income = monthly_transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0

    # If required, filter on categories
    category_filter = request.GET.get('category')
    if category_filter:
        transactions = transactions.filter(category_id=category_filter)

    selected_category = get_object_or_404(Category, id=category_filter) if category_filter else None

    # Filter transaction by type if required
    type_filter = request.GET.get('type')
    if type_filter == 'income':
        transactions = transactions.filter(is_income=True)
    elif type_filter == 'expense':
        transactions = transactions.filter(is_income=False)

    # Filter on title/description if required
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    categories = Category.objects.all()

    context = {
        'wallet': wallet,
        'transactions': transactions,
        'categories': categories,
        'current_category': category_filter,
        'selected_category': selected_category,
        'current_type': type_filter,
        'current_search': search_query,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
    }

    return render(request, 'wallet/transaction_list.html', context)

@login_required
def future_transaction_list(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)

    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    future_transactions = FutureTransaction.objects.filter(wallet=wallet, active=True).order_by('execution_date')

    context = {
        'wallet': wallet,
        'future_transactions': future_transactions,
    }

    return render(request, 'wallet/future_transaction_list.html', context)

@login_required
def edit_future_transaction(request, wallet_id, transaction_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    future_transaction = get_object_or_404(FutureTransaction, id=transaction_id, wallet=wallet)

    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    if request.method == 'POST':
        form = FutureTransactionForm(request.POST, instance=future_transaction)
        if form.is_valid():
            form.save()
            messages.success(request, _("future_transaction_updated_successfully"))
            return redirect('wallet:future_transaction_list', wallet_id=wallet.id)

    else:
        form = FutureTransactionForm(instance=future_transaction)

    context = {
        'form': form,
        'wallet': wallet,
        'future_transaction': future_transaction,
        'is_edit': True,
    }

    return render(request, 'wallet/add_future_transaction.html', context)

@login_required
def delete_future_transaction(request, wallet_id, transaction_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    future_transaction = get_object_or_404(FutureTransaction, id=transaction_id, wallet=wallet)

    if request.method == 'POST':
        future_transaction.delete()
        return redirect('wallet:future_transaction_list', wallet_id=wallet.id)

    return render(request, 'wallet/delete_future_transaction.html', {
        'future_transaction': future_transaction,
        'wallet': wallet
    })

@login_required
def edit_objective(request, wallet_id):
    """
    View to edit the objective of the wallet
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the wallet
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

    # Compute statistics on the objective
    current_progress = 0
    if wallet.objective > 0:
        current_progress = min((wallet.balance / wallet.objective) * 100, 100)

    # Suggestion of objectives base on the current balance
    suggested_objectives = []
    if wallet.balance > 0:
        suggested_objectives = [
            wallet.balance * Decimal('1.5'),  # 50% more
            wallet.balance * Decimal('2'),  # Double
            wallet.balance * Decimal('2.5'),  # 150% more
            round(wallet.balance, -2) + Decimal('500'),  # Rounded + 500
        ]
        # Delete doubles
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
    View to add a new family member to the wallet
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the wallet
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
    View to delete a member from the wallet
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check that the user is a member of the wallet
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


@login_required
def generate_monthly_report(request, wallet_id):
    """
    Generate a monthly PDF report
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check if user has access to the wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    # Calculate dates for current month
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return _generate_report(request, wallet, start_of_month, now, _('monthly'))


@login_required
def generate_quarterly_report(request, wallet_id):
    """
    Generate a quarterly PDF report
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check if user has access to the wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    # Calculate dates for current quarter
    now = timezone.now()
    current_quarter = (now.month - 1) // 3 + 1
    start_of_quarter = now.replace(month=(current_quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0,
                                   microsecond=0)

    return _generate_report(request, wallet, start_of_quarter, now, _('quarterly'))


@login_required
def generate_annual_report(request, wallet_id):
    """
    Generate an annual PDF report
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)

    # Check if user has access to the wallet
    if request.user not in wallet.users.all():
        messages.error(request, _("no_access_to_wallet"))
        return redirect('wallet:wallet_list')

    # Calculate dates for current year
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    return _generate_report(request, wallet, start_of_year, now, _('annual'))


def _generate_report(request, wallet, start_date, end_date, period_type):
    """
    Private function to generate PDF reports
    """
    # Get transactions for the period
    transactions = Transaction.objects.filter(
        wallet=wallet,
        date__gte=start_date.date(),
        date__lte=end_date.date()
    ).order_by('-date')

    # Calculate statistics
    period_income = transactions.filter(is_income=True).aggregate(
        total=Sum('amount'))['total'] or 0
    period_expenses = transactions.filter(is_income=False).aggregate(
        total=Sum('amount'))['total'] or 0

    net_result = period_income - period_expenses

    # Statistics by category (expenses only)
    category_stats = (
        transactions.filter(is_income=False)
        .values('category__name')
        .annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        .order_by('-total')
    )

    # Statistics by user
    user_stats = []
    for user in wallet.users.all():
        user_transactions = transactions.filter(user=user)
        income_total = user_transactions.filter(is_income=True).aggregate(
            total=Sum('amount'))['total'] or 0
        expense_total = user_transactions.filter(is_income=False).aggregate(
            total=Sum('amount'))['total'] or 0
        transaction_count = user_transactions.count()

        if transaction_count > 0:  # Only include users with transactions
            user_stats.append({
                'user_name': user.get_full_name(),
                'income_total': income_total,
                'expense_total': expense_total,
                'transaction_count': transaction_count
            })

    # Sort by transaction count (descending)
    user_stats.sort(key=lambda x: x['transaction_count'], reverse=True)

    # Prepare context for template
    context = {
        'wallet': wallet,
        'period_type': period_type,
        'start_date': start_date,
        'end_date': end_date,
        'transactions': transactions,
        'period_income': period_income,
        'period_expenses': period_expenses,
        'net_result': net_result,
        'category_stats': category_stats,
        'user_stats': user_stats,
        'transaction_count': transactions.count(),
        'generated_at': timezone.now(),
        'generated_by': request.user,
    }

    # Generate PDF
    template = get_template('wallet/report_pdf.html')
    html = template.render(context)

    # Create PDF response
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        # Create filename
        filename = f"{_('report')}_{period_type}_{wallet.name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

        # Log event
        Event.objects.create(
            date=timezone.now(),
            content=_("report_generated") + f" ({period_type}): {wallet.name}",
            user=request.user,
            type='REPORT_GENERATE'
        )

        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    messages.error(request, _("error_generating_report"))
    return redirect('wallet:transaction_list', wallet_id=wallet.id)