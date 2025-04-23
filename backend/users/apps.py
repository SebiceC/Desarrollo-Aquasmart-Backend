from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals  # Asegúrate de que se cargue la señal
        from .signals import create_default_person_types,create_default_document_types
        post_migrate.connect(create_default_person_types, sender=self)
        post_migrate.connect(create_default_document_types, sender=self)