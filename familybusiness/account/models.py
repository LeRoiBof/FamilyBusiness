import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission, Group
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Create your models here.

class AccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError(_("email_is_required"))
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Account(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name=_("email"))
    first_name = models.CharField(max_length=50, verbose_name=_("first_name"))
    last_name = models.CharField(max_length=50, verbose_name=_("last_name"))
    role = models.CharField(max_length=50, default='user', verbose_name=_("role"))
    is_active = models.BooleanField(default=True, verbose_name=_("is_active"))
    is_staff = models.BooleanField(default=False, verbose_name=_("is_staff"))
    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    groups = models.ManyToManyField(Group, related_name='accounts_users', blank=True, verbose_name=_("groups"))
    user_permissions = models.ManyToManyField(Permission, related_name='accounts_users', blank=True, verbose_name=_("user_permissions"))

    class Meta:
        verbose_name = _("account")
        verbose_name_plural = _("accounts")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name=_("user"))
    token = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name=_("token"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created_at"))

    class Meta:
        verbose_name = _("password_reset_token")
        verbose_name_plural = _("password_reset_tokens")

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=15)