from django.contrib import admin
from auditlog.admin import LogEntryAdmin as BaseLogEntryAdmin
from auditlog.filters import ResourceTypeFilter, CIDFilter
from auditlog.mixins import LogEntryAdminMixin
from auditlog.models import LogEntry

# Esto quita la configuración por defecto que auditlog registra automáticamente
admin.site.unregister(LogEntry)

@admin.register(LogEntry)
class CustomLogEntryAdmin(BaseLogEntryAdmin):
    # Columnas que aparecerán en la lista
    list_display = [
        "created",         # fecha y hora
        "actor",           # usuario que hizo la acción
        "action",          # tipo de acción (create/update/delete)
        "content_type",    # modelo afectado
        "msg_short",       # descripción breve
        "changes_summary",  # resumen de cambios
    ]

    # Filtros laterales en la página
    list_filter = [
        "action",
        "content_type",
    ]

    # Campos sobre los que buscar por texto
    search_fields = [
        "actor__username",
        "msg",
        "object_repr",
    ]

    def changes_summary(self, obj):
        """
        Toma el diccionario obj.changes y lo convierte
        en un string tipo "campoA: old → new, campoB: old → new"
        """
        changes = obj.changes or {}
        return ", ".join(
            f"{field}: {vals[0]} → {vals[1]}" for field, vals in changes.items()
        )

    changes_summary.short_description = "Resumen de cambios"