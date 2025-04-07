from rest_framework import serializers
from .models import IoTDevice, DeviceType, VALVE_48_ID, VALVE_4_ID
from plots_lots.models import Plot, Lot
from django.core.validators import MaxValueValidator, MinValueValidator


class IoTDeviceSerializer(serializers.ModelSerializer):
    iot_id = serializers.CharField(read_only=True)  # ID generado automáticamente
    device_type = serializers.PrimaryKeyRelatedField(queryset=DeviceType.objects.all())  
    id_plot = serializers.PrimaryKeyRelatedField(queryset=Plot.objects.all(), allow_null=True, required=False, default=None)  
    id_lot = serializers.PrimaryKeyRelatedField(queryset=Lot.objects.all(), allow_null=True, required=False, default=None)  
    owner_name = serializers.CharField(required=False, allow_blank=True)  # ✅ Permite que se envíe en la petición
    device_type_name = serializers.CharField(source='device_type.name', read_only=True)
    actual_flow = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = IoTDevice
        fields = ['iot_id', 'id_plot', 'id_lot', 'name', 'device_type',
        'is_active', 'characteristics', 'owner_name',
        'device_type_name', 'actual_flow']

    def validate(self, data):
        """ Validación personalizada """
        id_plot = data.get('id_plot')
        id_lot = data.get('id_lot')
        device_type = data.get('device_type')
        owner_name = data.get('owner_name', '').strip()
        actual_flow = data.get('actual_flow')

        # Si `id_plot` tiene dueño y `owner_name` se envía en la petición, lanzar error
        if id_plot and id_plot.owner and owner_name:
            raise serializers.ValidationError({"owner_name": "El propietario ya se obtiene del predio y no debe enviarse manualmente."})

        # Si se asigna un lote pero no el predio
        if id_lot and not id_plot:
            raise serializers.ValidationError({
                "id_plot": "El lote fue asignado sin su predio correspondiente."
            })
        
        # Si `id_lot` está presente, validar que pertenece al `id_plot`
        if id_lot and id_plot and id_lot.plot != id_plot:
            raise serializers.ValidationError({
                "id_lot": "El lote no pertenece al predio especificado."
            })

        # Validar que el dispositivo sea una válvula
        if device_type.device_id in [VALVE_48_ID, VALVE_4_ID]:
            # Validaciones específicas para válvula de 48"
            if device_type.device_id == VALVE_48_ID:
                # Verificar que no exista otra válvula de 48"
                if IoTDevice.objects.filter(device_type_id=VALVE_48_ID).exists():
                    raise serializers.ValidationError(
                        "Ya existe una válvula de 48\" en el distrito."
                    )
                
                # La válvula de 48" no debe asignarse a ningún predio ni lote
                if id_plot or id_lot:
                    raise serializers.ValidationError(
                        "La válvula de 48\" no puede asignarse a predios ni lotes."
                    )
                
            # Validaciones específicas para válvula de 4"
            elif device_type.device_id == VALVE_4_ID:
                # Validar que se asigne a un predio o a un lote
                if not id_plot and not id_lot:
                    raise serializers.ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio o a un lote."
                    )
                
                # Validar que no haya más de una válvula de 4" por predio
                if id_plot and not id_lot:
                    queryset = IoTDevice.objects.filter(
                    device_type_id=VALVE_4_ID,
                    id_plot=id_plot,
                    id_lot__isnull=True
                )

                    if self.instance:  # Si es una actualización, excluir el dispositivo actual
                        queryset = queryset.exclude(iot_id=self.instance.iot_id)
                    if queryset.exists(): # Evaluar si ya existe una válvula de 4" asignada al predio
                        raise serializers.ValidationError(
                            "Ya existe una válvula asignada a este predio."
                        )
            
                # Validar que no haya más de una válvula de 4" por lote
                if id_lot:
                    queryset = IoTDevice.objects.filter(
                    device_type_id=VALVE_4_ID,
                    id_lot=id_lot
                )
                    if self.instance:  # Si es una actualización, excluir el dispositivo actual
                        queryset = queryset.exclude(iot_id=self.instance.iot_id)
                    if queryset.exists(): # Evaluar si ya existe una válvula de 4" asignada al lote
                        raise serializers.ValidationError(
                            "Ya existe una válvula asignada a este lote."
                        )
        else:
            # Para dispositivos que no son válvulas, actual_flow debe ser None
            if actual_flow is not None:
                raise serializers.ValidationError({
                    "actual_flow": "El caudal actual solo aplica para válvulas."
                })

        return data

    def create(self, validated_data):
        """ Crear el dispositivo IoT y establecer el owner_name según disponibilidad """
        id_plot = validated_data.get('id_plot', None)
        
        # Si hay predio y tiene dueño, establecer owner_name
        if id_plot and id_plot.owner:
            validated_data['owner_name'] = id_plot.owner.get_full_name()
        elif not validated_data.get('owner_name'):
            validated_data['owner_name'] = "Sin dueño"  # ✅ Valor predeterminado si está vacío

        return super().create(validated_data)

class IoTDeviceStatusSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = IoTDevice
        fields = ['is_active']
        read_only_fields = ['iot_id']  # iot_id no se puede modificar

class DeviceTypeSerializer(serializers.ModelSerializer):
    id_plot = serializers.PrimaryKeyRelatedField(
        queryset=Plot.objects.all(),
        allow_null=True,  # Permite valores NULL
        required=False  # No es obligatorio en la API
    )

    class Meta:
        model = DeviceType
        fields = '__all__'  # Incluir todos los campos

    def create(self, validated_data):
        """Genera automáticamente el `device_id`"""
        instance = DeviceType(**validated_data)
        instance.save()
        return instance

# 🔹 Actualizar el caudal de una válvula por iot_id
class UpdateValveFlowSerializer(serializers.ModelSerializer):
    actual_flow = serializers.FloatField(required=True, validators=[MinValueValidator(0), MaxValueValidator(180)])

    class Meta:
        model = IoTDevice
        fields = ['actual_flow']

    def validate(self, data):
        device = self.instance  # Accede a la instancia actual del dispositivo
        
        if not device:
            raise serializers.ValidationError("Dispositivo no encontrado")
        
        # Valida que el dispositivo sea una válvula usando la instancia, no los datos de entrada
        if device.device_type.device_id not in [VALVE_48_ID, VALVE_4_ID]:
            raise serializers.ValidationError("Solo se puede actualizar el caudal para válvulas.")
        
        return data