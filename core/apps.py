# In core/apps.py (or banking/apps.py after rename)
from django.apps import AppConfig

class BankingConfig(AppConfig):  # Or CoreConfig if keeping 'core'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # This must match what's in INSTALLED_APPS