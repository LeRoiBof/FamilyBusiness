from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Wallet, Category, Transaction

class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['name', 'users', 'balance']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('wallet_name_placeholder')
            }),
            'users': forms.CheckboxSelectMultiple(attrs={
                'class': 'checkbox-group'
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'name': _('wallet_name'),
            'users': _('authorized_users'),
            'balance': _('initial_balance'),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input is-primary',
                'placeholder': _('category_name_placeholder')
            }),
        }
        labels = {
            'name': _('category_name'),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'category', 'amount', 'description', 'is_income']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input is-rounded',
                'placeholder': _('transaction_title_placeholder')
            }),
            'category': forms.Select(attrs={
                'class': 'select is-fullwidth'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input is-rounded',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea is-rounded',
                'placeholder': _('description_optional_placeholder'),
                'rows': 3
            }),
            'is_income': forms.CheckboxInput(attrs={
                'class': 'switch is-rounded is-success'
            }),
        }
        labels = {
            'title': _('transaction_title'),
            'category': _('category'),
            'amount': _('amount'),
            'description': _('description'),
            'is_income': _('is_income_question'),
        }