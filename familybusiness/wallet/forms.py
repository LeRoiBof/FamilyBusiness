from pydoc import describe

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Wallet, Category, Transaction, FutureTransaction


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['name', 'balance']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('wallet_name_placeholder')
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
            'balance': _('initial_balance'),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input is-primary',
                'placeholder': _('category_name_placeholder')
            }),
            'color': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'icon': forms.Select(attrs={'class': 'select is-fullwidth'}),
        }
        labels = {
            'name': _('category_name'),
            'color': _('color'),
            'icon': _('icon'),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'category', 'amount', 'date', 'description', 'is_income']
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
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input is-rounded'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea is-rounded',
                'placeholder': _('description_optional_placeholder'),
                'rows': 3
            }),
            'is_income': forms.CheckboxInput(attrs={
                'class': 'switch is-rounded is-success'
            })
        }
        labels = {
            'title': _('transaction_title'),
            'category': _('category'),
            'amount': _('amount'),
            'date': _('date'),
            'description': _('description'),
            'is_income': _('is_income_question'),
        }


class FutureTransactionForm(forms.ModelForm):
    class Meta:
        model = FutureTransaction
        fields = ['title', 'category', 'amount', 'description', 'is_income', 'execution_date', 'frequency']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': _('transaction_title_placeholder')}),
            'category': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'is_income': forms.CheckboxInput(attrs={'class': 'switch is-rounded is-success'}),
            'execution_date': forms.DateTimeInput(attrs={'class': 'input', 'type': 'datetime-local'}),
            'frequency': forms.Select(attrs={'class': 'select is-fullwidth'}),
        }
        labels = {
            'title': _('transaction_title'),
            'category': _('category'),
            'amount': _('amount'),
            'description': _('description'),
            'is_income': _('is_income_question'),
            'execution_date': _('execution_date'),
            'frequency': _('frequency'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['frequency'].choices = list(FutureTransaction.Frequency.choices)



class InvitationForm(forms.Form):
    """Form to generate an invitation link"""
    # No visible fields, only for CSRF validation
    pass