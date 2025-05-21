from rest_framework import serializers
from auditlog.models import LogEntry
from auditlog.mixins import LogEntryAdminMixin
from auditlog.filters import ResourceTypeFilter, CIDFilter

class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()  # Muestra el username del actor
    content_type = serializers.StringRelatedField()  # Muestra el nombre del modelo
    changes_summary = serializers.SerializerMethodField()
    created = serializers.DateTimeField(source='timestamp')
    
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
    
    def get_changes_summary(self, obj):
        changes = obj.changes or {}
        return [
            {
                'field': field,
                'old': vals[0],
                'new': vals[1]
            }
            for field, vals in changes.items()
        ]

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