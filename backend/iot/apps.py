from django.apps import AppConfig

class IotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iot'

    def ready(self):
        import iot.signals  # Registrar las señales