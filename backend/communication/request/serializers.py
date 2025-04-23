from django.utils import timezone
from rest_framework import serializers
from .models import FlowChangeRequest
from iot.models import VALVE_4_ID

class FlowChangeRequestSerializer(serializers.ModelSerializer):
    """Serializer para crear solicitudes de cambio de caudal."""

    class Meta:
        model = FlowChangeRequest
        fields = '__all__'
        read_only_fields = ['user', 'lot', 'plot', 'status', 'created_at', 'reviewed_at']

    def validate(self, attrs):
        device = attrs.get('device')
        user = self.context['request'].user

        # Asignar lote y predio automáticamente
        if device:
            if not attrs.get('lot') and hasattr(device, 'id_lot'):
                attrs['lot'] = device.id_lot
            if not attrs.get('plot') and hasattr(device, 'id_plot'):
                attrs['plot'] = device.id_plot

        # Validar que las solicitudes sean para válvulas de 4"
        device_type = device.device_type
        if device_type.device_id not in VALVE_4_ID:
            raise serializers.ValidationError(
                {"error": "Solo se puede solicitar cambios de caudal en dispositivos de tipo Válvula 4\""}
            )

        # Validar que el usuario sea dueño del predio
        plot = attrs.get('plot')
        if plot and hasattr(plot, 'owner'):
            if plot.owner != user:
                raise serializers.ValidationError(
                    {"error": "Solo el dueño del predio puede solicitar el cambio de caudal para este dispositivo."}
                )

        # Validación de caudal igual al actual
        requested_flow = attrs.get('requested_flow')
        if device and requested_flow is not None:
            if device.actual_flow == requested_flow:
                raise serializers.ValidationError(
                    {"requested_flow": "Ya tienes un caudal activo con ese valor. Debes solicitar un valor diferente."}
                )
        return attrs

    def create(self, validated_data):
        # Asignar usuario automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class FlowChangeRequestStatusSerializer(serializers.ModelSerializer):
    """Serializer para actualizar el estado de la solicitud de cambio de caudal."""

    class Meta:
        model = FlowChangeRequest
        fields = ['status', 'reviewed_at']
        read_only_fields = ['reviewed_at']

    def validate_status(self, value):
        if value not in ['aprobada', 'rechazada']:
            raise serializers.ValidationError("Solo se permite aprobar o rechazar la solicitud.")
        return value

    def update(self, instance, validated_data):
        if instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )
        validated_data['reviewed_at'] = timezone.now()
        return super().update(instance, validated_data)