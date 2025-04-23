from django.apps import AppConfig
from django.db.models.signals import post_migrate
class IotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iot'

    def ready(self):
        import iot.signals  # Registrar las señales
        from .signals import create_default_divice_types
        post_migrate.connect(create_default_divice_types,sender=self)