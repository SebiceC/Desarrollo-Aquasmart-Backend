from rest_framework import serializers
from auditlog.models import LogEntry
from auditlog.mixins import LogEntryAdminMixin
from auditlog.filters import ResourceTypeFilter, CIDFilter


class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()  # Muestra el username del actor
    content_type = serializers.StringRelatedField()  # Muestra el nombre del modelo
    changes_summary = serializers.SerializerMethodField()
    created = serializers.DateTimeField(source='timestamp')
    action = serializers.SerializerMethodField()
    
    class Meta:
        model = LogEntry
        fields = [
            'id',
            'created',
            'actor',
            'action',
            'content_type',
            'object_repr',
            'changes_summary',
            'remote_addr',
        ]

    def get_action(self, obj):
        """Convierte el número de acción en string"""
        action_map = {
            0: 'create',
            1: 'update',
            2: 'delete',
            3: 'access'
        }
        return action_map.get(obj.action, 'unknown')

    def get_changes_summary(self, obj):
        changes = obj.changes or {}
        summary = []
        
        for field, vals in changes.items():
            if isinstance(vals, (list, tuple)) and len(vals) >= 2:
                # Formato [old_value, new_value]
                summary.append({
                    'field': field,
                    'old': vals[0],
                    'new': vals[1]
                })
            elif isinstance(vals, dict) and 'old' in vals and 'new' in vals:
                # Formato {'old': old_value, 'new': new_value}
                summary.append({
                    'field': field,
                    'old': vals['old'],
                    'new': vals['new']
                })
            else:
                # Otro formato: mostrar el valor tal cual
                summary.append({
                    'field': field,
                    'old': str(vals),
                    'new': str(vals)
                })

        return summary


class MyLogEntryAdminMixin(LogEntryAdminMixin):
    def get_list_display(self, request):
        return [
            "created",         # fecha/hora
            "user_url",        # link al usuario
            "action",          # create/update/delete
            "resource_url",    # link al objeto auditable
            "msg_short",       # breve descripción
        ]

    def get_list_filter(self, request):
        return [
            "action",
            ResourceTypeFilter,
            # CIDFilter,      # si quieres filtro de correlation ID
        ]

    def get_search_fields(self, request):
        return [
            "actor__username",
            "object_repr",
            "changes",
        ]

    def get_readonly_fields(self, request, obj=None):
        # si quieres cambiar campos de solo lectura en el detalle
        return ["created", "user_url", "resource_url", "msg"]