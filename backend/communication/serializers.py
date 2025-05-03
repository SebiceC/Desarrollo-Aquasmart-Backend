from django.utils import timezone
from rest_framework import serializers
from .request.models import BaseFlowRequest
from iot.models import IoTDevice, VALVE_4_ID

class BaseFlowRequestSerializer(serializers.ModelSerializer):
    """Serializer base para solicitudes de caudal."""

    class Meta:
        model = BaseFlowRequest
        fields = '__all__'
        read_only_fields = 'status'
        extra_kwargs = {
        'lot': {'required': True, 'allow_null': False}
    }

    def validate_lot(self, value):
        ''' Validaciones del lote en la solicitud '''
        valve = IoTDevice.objects.filter(id_lot=value, device_type__device_id=VALVE_4_ID).first()
        # Validar que el lote no tenga una válvula de 4" asociada
        if not valve:
            raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")
        # Valida que el lote en cuya solicitud está presente, esté habilitado
        if value.is_activate == False:
            raise serializers.ValidationError("No se puede realizar solicitud de caudal de un lote inhabilitado.")
        return value

    def validate_requested_flow(self, value):
        ''' Valida que el caudal solicitado sea válido '''
        if value < 1 or value >= 11.7:
            raise serializers.ValidationError("El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        lot = attrs.get('lot')

        # Validar que el usuario (solicitante) sea dueño del predio
        if lot:
            if user != lot.plot.owner:
                raise serializers.ValidationError(
                    {"owner": "Solo el dueño del predio puede realizar una solicitud para el caudal de este lote."}
                )

        return attrs

    def create(self, validated_data):
        # Asignar el usuario (solicitante) automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Verificar si solicita un 'status' que ya fue asignada
        if instance.status == validated_data['status']:
            raise serializers.ValidationError(
                {"status": f"La solicitud ya fue {validated_data['status']}."}
            )
        # Impedir que se pueda cambiar el estado una vez revisada la solicitud
        elif instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )

        validated_data['reviewed_at'] = timezone.now()


class BaseRequestStatusSerializer(serializers.ModelSerializer):
    """Serializer base para actualizar el estado de solicitudes de caudal."""

    class Meta:
        model = BaseFlowRequest
        fields = ['status', 'reviewed_at']
        read_only_fields = ['reviewed_at']

    def _validate_lot(self):
        ''' Validaciones del lote en la solicitud '''
        lot = getattr(self.instance, 'lot', None)
        valve = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        # Validar que el lote no tenga una válvula de 4" asociada
        if not valve:
            raise serializers.ValidationError(
                {"error": "El lote no tiene una válvula 4\" asociada."}
            )
        # Valida que el lote en cuya solicitud está presente, esté habilitado
        if lot.is_activate == False:
            raise serializers.ValidationError(
                {"error": "No se puede aprobar/rechazar una solicitud de caudal de un lote inhabilitado."
            })

    def validate_status(self, value):
        ''' Valida que el estado sea 'aprobada' o 'rechazada' '''
        if value not in ['aprobada', 'rechazada']:
            raise serializers.ValidationError("Solo se permite aprobar o rechazar la solicitud.")
        return value

    def validate(self, attrs):
        self._validate_lot()

        return attrs

    def create(self, validated_data):
        # Asignar el usuario (solicitante) automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Verificar si solicita un 'status' que ya fue asignada
        if instance.status == validated_data['status']:
            raise serializers.ValidationError(
                {"status": f"La solicitud ya fue {validated_data['status']}."}
            )
        # Impedir que se pueda cambiar el estado una vez revisada la solicitud
        elif instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )

        validated_data['reviewed_at'] = timezone.now()

        return super().update(instance, validated_data)