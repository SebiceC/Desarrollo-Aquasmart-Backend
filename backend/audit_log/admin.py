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
        Maneja diferentes formatos de datos en el campo changes
        """
        changes = obj.changes or {}
        summary = []
        
        for field, vals in changes.items():
            if isinstance(vals, (list, tuple)) and len(vals) >= 2:
                # Formato [old_value, new_value]
                summary.append(f"{field}: {vals[0]} → {vals[1]}")
            elif isinstance(vals, dict) and 'old' in vals and 'new' in vals:
                # Formato {'old': old_value, 'new': new_value}
                summary.append(f"{field}: {vals['old']} → {vals['new']}")
            else:
                # Otro formato: mostrar el valor tal cual
                summary.append(f"{field}: {vals}")
        
        return ", ".join(summary) if summary else "Sin cambios"

    changes_summary.short_description = "Resumen de cambios"