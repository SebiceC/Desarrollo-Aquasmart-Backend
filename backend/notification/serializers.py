from rest_framework import serializers
from .models import Notification
from users.serializers import CustomUserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    recipient = CustomUserSerializer(read_only=True)
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'content_object',
            'recipient',
            'created_at',
            'is_read',
            'metadata'
        ]
        read_only_fields = fields

    def get_content_object(self, obj):
        """
        Versión genérica que devuelve el ID y tipo del objeto relacionado
        """
        if obj.content_object:
            return {
                'id': obj.content_object.id,
                'type': obj.content_type.model,
                'repr': str(obj.content_object)
            }
        return None