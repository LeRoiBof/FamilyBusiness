# Créez ce fichier avec la commande :
# python manage.py makemigrations --empty wallet

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """
    Create default categories for the application
    """
    Category = apps.get_model('wallet', 'Category')

    default_categories = [
        'Alimentation',
        'Transport',
        'Logement',
        'Santé',
        'Loisirs',
        'Vêtements',
        'Éducation',
        'Services',
        'Épargne',
        'Revenus',
        'Cadeaux',
        'Voyages',
        'Assurances',
        'Taxes',
        'Autres'
    ]

    for category_name in default_categories:
        Category.objects.get_or_create(name=category_name)


def remove_default_categories(apps, schema_editor):
    """
    Remove default categories (reverse operation)
    """
    Category = apps.get_model('wallet', 'Category')

    default_categories = [
        'Alimentation', 'Transport', 'Logement', 'Santé', 'Loisirs',
        'Vêtements', 'Éducation', 'Services', 'Épargne', 'Revenus',
        'Cadeaux', 'Voyages', 'Assurances', 'Taxes', 'Autres'
    ]

    Category.objects.filter(name__in=default_categories).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('wallet', '0003_walletinvitation'),
    ]

    operations = [
        migrations.RunPython(
            create_default_categories,
            remove_default_categories
        ),
    ]