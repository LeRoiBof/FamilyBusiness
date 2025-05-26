from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

Account = get_user_model()

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Mot de passe'
        }),
        min_length=8
    )

    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Confirmer le mot de passe'
        })
    )

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom de famille',
            'email': 'Adresse email',
            'is_staff': "Droits d'administration",
            'is_active': 'Compte actif',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Nom de famille'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'email@exemple.com'
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
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Les mots de passe ne correspondent pas.")
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
            'first_name': 'Prénom',
            'last_name': 'Nom de famille',
            'email': 'Adresse email',
            'is_staff': "Droits d'administration",
            'is_active': 'Compte actif',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nom de famille'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'email@exemple.com'}),
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
            raise ValidationError("Cet email est déjà utilisé.")
        return email

