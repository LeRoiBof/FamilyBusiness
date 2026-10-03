import uuid
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Wallet(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    owner = models.ForeignKey('account.Account', on_delete=models.CASCADE, verbose_name=_("owner"))
    users = models.ManyToManyField('account.Account', related_name='wallets', blank=True, verbose_name=_("users"))
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("balance"))
    objective = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name=_("objective"))

    class Meta:
        verbose_name = _("wallet")
        verbose_name_plural = _("wallets")

    def __str__(self):
        return self.name

class WalletInvitation(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='invitations')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_by = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey('account.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invitations')
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("wallet_invitation")
        verbose_name_plural = _("wallet_invitations")

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"Invitation to {self.wallet.name} - {self.token}"

class Category(models.Model):
    COLOR_CHOICES = [
        ('primary', _('color_primary')),
        ('success', _('color_success')),
        ('warning', _('color_warning')),
        ('danger', _('color_danger')),
        ('info', _('color_info')),
        ('light', _('color_light')),
    ]

    COLOR_HEX = {
        'primary': '#00d1b2',
        'success': '#48c78e',
        'warning': '#ffdd57',
        'danger': '#f14668',
        'info': '#3273dc',
        'light': '#f5f5f5',
    }

    ICON_CHOICES = [
        ('mdi-tag', _('icon_other')),
        ('mdi-cart', _('icon_shopping')),
        ('mdi-home', _('icon_housing')),
        ('mdi-car', _('icon_transport')),
        ('mdi-medical-bag', _('icon_health')),
        ('mdi-silverware-fork-knife', _('icon_food')),
        ('mdi-gift-outline', _('icon_gift')),
        ('mdi-cash', _('icon_salary')),
        ('mdi-piggy-bank-outline', _('icon_savings')),
        ('mdi-dumbbell', _('icon_leisure')),
        ('mdi-school-outline', _('icon_education')),
        ('mdi-toolbox-outline', _('icon_services')),
        ('mdi-shield-check-outline', _('icon_insurance')),
        ('mdi-receipt-text-outline', _('icon_taxes')),
        ('mdi-airplane', _('icon_travel')),
        ('mdi-hanger', _('icon_clothing')),
        ('mdi-bank-transfer', _('icon_transfer')),
    ]

    name = models.CharField(max_length=100, verbose_name=_("name"))
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='primary', verbose_name=_("color"))
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='mdi-tag', verbose_name=_("icon"))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name

    def get_color_hex(self):
        return self.COLOR_HEX.get(self.color, self.COLOR_HEX['primary'])

class Transaction(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("title"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("category"))
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, verbose_name=_("user"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("amount"))
    date = models.DateField(default=timezone.localdate, verbose_name=_("date"))
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("wallet"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    is_income = models.BooleanField(default=False, verbose_name=_("is_income"))
    is_transfer = models.BooleanField(default=False, verbose_name=_("is_transfer"))
    linked_transaction = models.OneToOneField(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name=_("linked_transaction")
    )

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    def __str__(self):
        return f"{self.title} - {self.amount}€ - {self.date}"


class FutureTransaction(models.Model):
    class Frequency(models.TextChoices):
        ONCE = "once", _("once")
        DAILY = "daily", _("daily")
        WEEKLY = "weekly", _("weekly")
        MONTHLY = "monthly", _("monthly")
        YEARLY = "yearly", _("yearly")

    title = models.CharField(max_length=100, verbose_name=_("title"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("category"))
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, verbose_name=_("user"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("amount"))
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="future_transactions" ,verbose_name=_("wallet"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    is_income = models.BooleanField(default=False, verbose_name=_("is_income"))
    execution_date = models.DateTimeField(verbose_name=_("execution date"))
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.ONCE, verbose_name=_("frequency"))
    active = models.BooleanField(default=True, verbose_name=_("active"))

    class Meta:
        verbose_name = _("future transaction")
        verbose_name_plural = _("future transactions")

    def __str__(self):
        return f"{self.title} - {self.amount}€ on {self.execution_date} ({self.frequency})"

    def create_transaction(self):
        Transaction.objects.create(
            title=self.title,
            category=self.category,
            user=self.user,
            amount=self.amount,
            wallet=self.wallet,
            description=self.description,
            is_income=self.is_income,
            date=self.execution_date,
        )

    def get_next_execution_date(self):

        if self.frequency == FutureTransaction.Frequency.ONCE:
            return None

        if self.frequency == FutureTransaction.Frequency.DAILY:
            return self.execution_date + timedelta(days=1)
        elif self.frequency == FutureTransaction.Frequency.WEEKLY:
            return self.execution_date + timedelta(weeks=1)
        elif self.frequency == FutureTransaction.Frequency.MONTHLY:
            return self.execution_date + relativedelta(months=+1)
        elif self.frequency == FutureTransaction.Frequency.YEARLY:
            return self.execution_date + relativedelta(years=+1)

        return None