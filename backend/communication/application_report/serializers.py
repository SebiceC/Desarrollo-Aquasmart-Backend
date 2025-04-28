from rest_framework import serializers
from .models import ApplicationFailureReport

class ApplicationFailureReportSerializer(serializers.ModelSerializer):
    """Serializer para crear reportes de fallos en el aplicativo."""

    class Meta:
        model = ApplicationFailureReport
        fields = ['id', 'observations', 'status', 'created_at', 'reviewed_at']
        read_only_fields = ['user']  # El campo user es de solo lectura

    def validate_observations(self, value):
        if not value or len(value) > 200:
            raise serializers.ValidationError("Las observaciones son obligatorias y no pueden exceder los 200 caracteres.")
        return value

    def create(self, validated_data):
        # Asigna automáticamente el usuario actual a partir del contexto de la solicitud
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)  