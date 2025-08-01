from datetime import date

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils.translation import gettext as _
from .forms import RegistrationForm, LoginForm, ResetPasswordForm, CustomPasswordChangeForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from adminpanel.models import Event
from .models import Account, PasswordResetToken

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            Event.objects.create(
                date=date.today(),
                content=_("new_account_created_for") + f" {form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
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
                content=_("login_for") + f" {user.first_name} {user.last_name}",
                user=user,
                type='LOGIN'
            )
            invitation_token = request.session.get('invitation_token')
            if invitation_token:
                # Delete session token
                del request.session['invitation_token']
                # Redirect to invite acceptance
                return redirect('wallet:accept_invitation', token=invitation_token)
            else:
                return redirect('home:home')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})

def logout_view(request):
    Event.objects.create(
        date=date.today(),
        content=_("logout_for") + f" {request.user.first_name} {request.user.last_name}",
        user=request.user,
        type='LOGOUT'
    )
    logout(request)
    return redirect('account:login')

def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = Account.objects.filter(email=email).first()
        if user:
            token = PasswordResetToken.objects.create(user=user)
            return render(request, 'account/token_display.html', {'token': token.token})
        messages.error(request, _("no_account_with_this_email"))
    return render(request, 'account/request_password_reset.html')


def reset_password(request, token):
    token_obj = get_object_or_404(PasswordResetToken, token=token)
    if not token_obj.is_valid():
        messages.error(request, _("token_expired"))
        return redirect('account:request_password_reset')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            token_obj.user.set_password(form.cleaned_data['password'])
            token_obj.user.save()
            token_obj.delete()
            messages.success(request, _("password_reset_successfully"))
            return redirect('account:login')
    else:
        form = ResetPasswordForm()

    return render(request, 'account/reset_password.html', {'form': form})

def generate_new_token(request, token):
    token_obj = get_object_or_404(PasswordResetToken, token=token)
    if not token_obj.is_valid():
        messages.error(request, _("token_expired"))
        return redirect('account:request_password_reset')

    new_token = PasswordResetToken.objects.create(user=token_obj.user)
    token_obj.delete()
    return render(request, 'account/token_display.html', {'token': new_token.token})


@login_required
def profile_view(request):
    """
    View for managing user profile
    """
    profile_form = ProfileUpdateForm(instance=request.user)
    password_form = CustomPasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                old_email = request.user.email
                profile_form.save()

                # Log the profile update event
                Event.objects.create(
                    date=date.today(),
                    content=_("profile_updated_for") + f" {request.user.get_full_name()}",
                    user=request.user,
                    type='PROFILE_UPDATE'
                )

                messages.success(request, _("profile_updated_successfully"))
                return redirect('account:profile')

        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Keep user logged in after password change
                update_session_auth_hash(request, user)

                # Log the password change event
                Event.objects.create(
                    date=date.today(),
                    content=_("password_changed_for") + f" {request.user.get_full_name()}",
                    user=request.user,
                    type='PASSWORD_CHANGE'
                )

                messages.success(request, _("password_changed_successfully"))
                return redirect('account:profile')

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }

    return render(request, 'account/profile.html', context)