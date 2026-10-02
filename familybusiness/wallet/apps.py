import os
import sys

from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wallet'

    def ready(self):
        is_runserver = 'runserver' in sys.argv or 'shell_plus' in sys.argv
        # Avec l'auto-reload de runserver, ready() tourne aussi dans le process
        # rechargeur (sans RUN_MAIN) : sans ce garde, le scheduler démarre deux fois
        # et les deux instances se marchent dessus sur le même sqlite ("database is locked").
        if is_runserver and os.environ.get('RUN_MAIN') != 'true':
            return
        if is_runserver:
            from . import scheduler
            scheduler.start()