from django.db import models

# Create your models here.

class Event(models.Model):

    TYPES = (
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('WALLET_CREATE', 'Création portefeuille'),
        ('WALLET_DELETE', 'Suppression portefeuille'),
        ('WALLET_UPDATE', 'Modification portefeuille'),
        ('TRANSACTION_CREATE', 'Ajout transaction'),
        ('TRANSACTION_DELETE', 'Suppression transaction'),
        ('TRANSACTION_UPDATE', 'Modification transaction'),
        ('OBJECTIVE_UPDATE', 'Modification objectif'),
        ('USER_REGISTER', 'Inscription utilisateur'),
        ('PASSWORD_CHANGE', 'Changement mot de passe'),
        ('ERROR', 'Erreur'),
        ('ADMIN_ACTION', 'Action admin'),
        ('OTHER', 'Autre')
    )

    date = models.DateField()
    content = models.TextField()
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPES)

    def __str__(self):
        return f"{self.type} - {self.date.strftime('%Y-%m-%d')} - {self.user.get_full_name()}"
