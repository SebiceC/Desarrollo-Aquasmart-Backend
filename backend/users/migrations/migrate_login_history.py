from django.db import migrations
from django.contrib.contenttypes.models import ContentType


def migrate_login_history(apps, schema_editor):
    LoginHistory = apps.get_model("users", "LoginHistory")
    LogEntry = apps.get_model("auditlog", "LogEntry")
    CustomUser = apps.get_model("users", "CustomUser")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # Obtener ContentType para CustomUser
    content_type = ContentType.objects.get_for_model(CustomUser)

    # Migrar cada registro de LoginHistory a LogEntry
    for login in LoginHistory.objects.all():
        LogEntry.objects.create(
            content_type_id=content_type.id,
            object_pk=str(login.user.pk),
            actor_id=login.user.pk,  # Usar pk en lugar de id
            action=0,  # 0 = CREATE en auditlog
            timestamp=login.timestamp,
            changes={},
        )


def reverse_migrate_login_history(apps, schema_editor):
    # No hacemos nada en la reversión
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(migrate_login_history, reverse_migrate_login_history),
    ]
