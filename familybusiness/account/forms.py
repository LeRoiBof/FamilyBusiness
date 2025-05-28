from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Account

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input'}), label=_("first_name"))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input'}), label=_("last_name"))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input'}), label=_("email"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label=_("password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label=_("confirm_password"))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("passwords_do_not_match"))

        return cleaned_data

    def save(self, commit=True):
        account = super().save(commit=False)
        account.set_password(self.cleaned_data['password1'])
        if commit:
            account.save()
        return account

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input'}), label=_("email"))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input'}), label=_("password"))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError(_("invalid_credentials"))
            if not self.user.is_active:
                raise forms.ValidationError(_("account_is_disabled"))
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label=_("new_password"),
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': _("minimum_8_characters"),
            'minlength': 8
        })
    )
    confirm_password = forms.CharField(
        label=_("confirm_password"),
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': _("retype_password")
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')

        if password and confirm and password != confirm:
            raise forms.ValidationError(_("passwords_do_not_match"))

        return cleaned_data