from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Event(models.Model):

    TYPES = (
        ('LOGIN', _('event_type_login')),
        ('LOGOUT', _('event_type_logout')),
        ('WALLET_CREATE', _('event_type_wallet_create')),
        ('WALLET_DELETE', _('event_type_wallet_delete')),
        ('WALLET_UPDATE', _('event_type_wallet_update')),
        ('TRANSACTION_CREATE', _('event_type_transaction_create')),
        ('TRANSACTION_DELETE', _('event_type_transaction_delete')),
        ('TRANSACTION_UPDATE', _('event_type_transaction_update')),
        ('TRANSACTION_EXPORT', _('event_type_transaction_export')),
        ('OBJECTIVE_UPDATE', _('event_type_objective_update')),
        ('USER_REGISTER', _('event_type_user_register')),
        ('PASSWORD_CHANGE', _('event_type_password_change')),
        ('ERROR', _('event_type_error')),
        ('ADMIN_ACTION', _('event_type_admin_action')),
        ('OTHER', _('event_type_other'))
    )

    date = models.DateField(verbose_name=_("date"))
    content = models.TextField(verbose_name=_("content"))
    type = models.CharField(max_length=50, choices=TYPES, verbose_name=_("type"))
    user = models.ForeignKey(
        'account.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_("user")
    )

    user_name_snapshot = models.CharField(max_length=255, blank=True, verbose_name=_("user_name_snapshot"))

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        user_display = self.user.get_full_name() if self.user else self.user_name_snapshot or _("deleted_user")
        return f"{self.type} - {self.date.strftime('%Y-%m-%d')} - {user_display}"