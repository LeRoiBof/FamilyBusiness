from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Account

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input'}), label="Prénom")
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input'}), label="Nom")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input'}), label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label="Mot de passe")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label="Confirmer le mot de passe")

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas")

        return cleaned_data

    def save(self, commit=True):
        account = super().save(commit=False)
        account.set_password(self.cleaned_data['password1'])
        if commit:
            account.save()
        return account

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input'}), label="Email")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label="Mot de passe")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Identifiants invalides.")
            if not self.user.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Minimum 8 caractères', 'minlength': 8})
    )
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Retapez le mot de passe'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')

        if password and confirm and password != confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data