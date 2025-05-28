from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Wallet(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    owner = models.ForeignKey('account.Account', on_delete=models.CASCADE, verbose_name=_("owner"))
    users = models.ManyToManyField('account.Account', related_name='wallets', blank=True, verbose_name=_("users"))
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("balance"))
    objective = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("objective"))

    class Meta:
        verbose_name = _("wallet")
        verbose_name_plural = _("wallets")

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name

class Transaction(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("title"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("category"))
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, verbose_name=_("user"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("amount"))
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("wallet"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    is_income = models.BooleanField(default=False, verbose_name=_("is_income"))

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    def __str__(self):
        return f"{self.title} - {self.amount}€ - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"