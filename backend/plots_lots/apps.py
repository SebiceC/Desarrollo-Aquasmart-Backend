from django.apps import AppConfig
from django.db.models.signals import post_migrate

class PlotsLotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plots_lots'

    def ready(self):
        from .signals import create_default_crop_types, create_default_soilt_types
        post_migrate.connect(create_default_soilt_types,sender=self)
        post_migrate.connect(create_default_crop_types,sender=self)