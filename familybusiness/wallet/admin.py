from django.contrib import admin
from .models import Wallet, Transaction, Category

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'balance', 'objective')
    list_filter = ('owner',)
    search_fields = ('name', 'owner__email', 'users__email')
    filter_horizontal = ('users',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'wallet', 'user', 'amount', 'is_income', 'date')
    list_filter = ('is_income', 'wallet', 'category', 'user')
    search_fields = ('title', 'description', 'wallet__name', 'user__email')
    date_hierarchy = 'date'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
