from communication.serializers import BaseFlowRequestSerializer, BaseRequestStatusSerializer
from .models import WaterSupplyFailureReport
from rest_framework import serializers

class WaterSupplyFailureReportSerializer(BaseFlowRequestSerializer):
    """Serializer para crear reportes de fallos en suministro de agua."""

    class Meta(BaseFlowRequestSerializer.Meta):
        model = WaterSupplyFailureReport
        fields = '__all__'
        read_only_fields = ['user', 'status', 'created_at', 'reviewed_at']
        extra_kwargs = {'lot': {'required': False, 'allow_null': True}}

    def validate_observations(self, value):
        if not value or len(value) > 200:
            raise serializers.ValidationError("Las observaciones son obligatorias y no pueden exceder los 200 caracteres.")
        return value

    def _validate_pending_report_lot(self, lot):
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if WaterSupplyFailureReport.objects.filter(lot=lot, status='pendiente').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "Reporte pendiente detectado en el lote. Verifique sus reportes pendientes o en proceso."}
            )

    def _validate_pending_report_plot(self, plot):
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if WaterSupplyFailureReport.objects.filter(lot=None, plot=plot, status='pendiente').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "Reporte pendiente detectado en el predio. Verifique sus reportes pendientes o en proceso."}
            )

    def validate(self, attrs):
        user = self.context['request'].user
        lot = attrs.get('lot')
        plot = attrs.get('plot')

        # Validar que el usuario (solicitante) sea dueño del predio
        if lot:
            if user != lot.plot.owner:
                raise serializers.ValidationError(
                    {"owner": "Solo el dueño del predio puede realizar una solicitud para el caudal de este lote."}
                )
        elif plot:
            if user != plot.owner:
                raise serializers.ValidationError(
                    {"owner": "Solo el dueño del predio puede realizar una solicitud para el caudal de este lote."}
                )


        # No se permite que ambos estén vacíos
        if not lot and not plot:
            raise serializers.ValidationError(
                {"error": "Se debe especificar un lote o un predio para el reporte."}
            )

        # No se permite que ambos estén presentes
        if lot and plot:
            raise serializers.ValidationError(
                {"error": "Solo se debe especificar un lote o un predio, no ambos."}
            )

        if lot:
            self._validate_pending_report_lot(lot)
        if plot:
            self._validate_pending_report_plot(plot)

        return attrs

class WaterSupplyFailureReportStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de un reporte de fallo de suministro de agua."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = WaterSupplyFailureReport
