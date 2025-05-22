from django.db import models

# Create your models here.

class Wallet(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    users = models.ManyToManyField('account.Account', related_name='wallets', blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    objective = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    title = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    description = models.TextField(blank=True)
    is_income = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.amount}€ - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
