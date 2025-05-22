from django import forms
from .models import Wallet, Category, Transaction

class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['name', 'users', 'balance']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Nom du portefeuille'
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
            'name': 'Nom du portefeuille',
            'users': 'Utilisateurs autorisés',
            'balance': 'Solde initial',
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input is-primary',
                'placeholder': 'Nom de la catégorie'
            }),
        }
        labels = {
            'name': 'Nom de la catégorie',
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'category', 'amount', 'description', 'is_income']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input is-rounded',
                'placeholder': 'Titre de la transaction'
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
                'placeholder': 'Description (optionnel)',
                'rows': 3
            }),
            'is_income': forms.CheckboxInput(attrs={
                'class': 'switch is-rounded is-success'
            }),
        }
        labels = {
            'title': 'Titre de la transaction',
            'category': 'Catégorie',
            'amount': 'Montant',
            'description': 'Description',
            'is_income': 'Revenus ?',
        }