from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

Account = get_user_model()

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label=_("password"),
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': _("password")
        }),
        min_length=8
    )

    confirm_password = forms.CharField(
        label=_("confirm_password"),
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': _("confirm_password")
        })
    )

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'first_name': _("first_name"),
            'last_name': _("last_name"),
            'email': _("email_address"),
            'is_staff': _("admin_rights"),
            'is_active': _("active_account"),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _("first_name")
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _("last_name")
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': _("email_example")
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise ValidationError(_("email_already_used"))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error("confirm_password", _("passwords_do_not_match"))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'first_name': _("first_name"),
            'last_name': _("last_name"),
            'email': _("email_address"),
            'is_staff': _("admin_rights"),
            'is_active': _("active_account"),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': _("first_name")}),
            'last_name': forms.TextInput(attrs={'class': 'input', 'placeholder': _("last_name")}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': _("email_example")}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        self.current_user_id = kwargs.pop('current_user_id', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = Account.objects.filter(email=email).exclude(id=self.current_user_id).first()
        if existing_user:
            raise ValidationError(_("email_already_used"))
        return email