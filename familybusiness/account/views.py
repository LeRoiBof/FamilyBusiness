from datetime import date

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegistrationForm, LoginForm
from django.contrib.auth.decorators import login_required
from adminpanel.models import Event

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            Event.objects.create(
                date=date.today(),
                content=f"Nouveau compte créé pour {form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                user=form.instance,
                type='USER_REGISTER'
            )
            return redirect('account:login')
    else:
        form = RegistrationForm()
    return render(request, 'account/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            Event.objects.create(
                date=date.today(),
                content=f"Connexion de {user.first_name} {user.last_name}",
                user=user,
                type='LOGIN'
            )
            return redirect('home:home')
        else:
            messages.error(request, "Invalid login credentials.")
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})

def logout_view(request):
    Event.objects.create(
        date=date.today(),
        content=f"Déconnexion de {request.user.first_name} {request.user.last_name}",
        user=request.user,
        type='LOGOUT'
    )
    logout(request)
    return redirect('account:login')
