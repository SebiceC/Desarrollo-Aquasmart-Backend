from django.apps import AppConfig

class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'

    def ready(self):
        # Importación condicional para evitar errores durante las migraciones
        import sys
        if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
            try:
                from . import signals
            except Exception as e:
                print(f"Error importing signals: {e}")

class ReportesConfig(AppConfig):
    name = 'reportes'  # Asegúrate que coincida con el INSTALLED_APPS
    verbose_name = 'Reportes'