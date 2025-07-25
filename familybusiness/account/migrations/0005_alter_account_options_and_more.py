# Generated by Django 5.1.6 on 2025-05-27 09:05

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_passwordresettoken'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'verbose_name': 'account', 'verbose_name_plural': 'accounts'},
        ),
        migrations.AlterModelOptions(
            name='passwordresettoken',
            options={'verbose_name': 'password_reset_token', 'verbose_name_plural': 'password_reset_tokens'},
        ),
        migrations.AlterField(
            model_name='account',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='email'),
        ),
        migrations.AlterField(
            model_name='account',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='first_name'),
        ),
        migrations.AlterField(
            model_name='account',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='accounts_users', to='auth.group', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='account',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='is_active'),
        ),
        migrations.AlterField(
            model_name='account',
            name='is_staff',
            field=models.BooleanField(default=False, verbose_name='is_staff'),
        ),
        migrations.AlterField(
            model_name='account',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='last_name'),
        ),
        migrations.AlterField(
            model_name='account',
            name='role',
            field=models.CharField(default='user', max_length=50, verbose_name='role'),
        ),
        migrations.AlterField(
            model_name='account',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, related_name='accounts_users', to='auth.permission', verbose_name='user_permissions'),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='created_at'),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='token'),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
