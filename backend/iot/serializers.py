from rest_framework import serializers
from .models import IoTDevice, DeviceType, VALVE_48_ID, VALVE_4_ID
from plots_lots.models import Plot, Lot

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

        # 1️⃣ Si `id_plot` tiene dueño y `owner_name` se envía en la petición, lanzar error
        if id_plot and id_plot.owner and owner_name:
            raise serializers.ValidationError({"owner_name": "El propietario ya se obtiene del predio y no debe enviarse manualmente."})

        # 2️⃣ Si `id_lot` está presente, validar que pertenece al `id_plot`
        if id_lot and id_plot and id_lot.plot != id_plot:
            raise serializers.ValidationError({
                "id_lot": "El lote no pertenece al predio especificado."
            })

        # Validaciones específicas para válvulas
        if device_type.device_id in [VALVE_48_ID, VALVE_4_ID]:
            # Validar que actual_flow esté presente para válvulas
            if actual_flow is None:
                raise serializers.ValidationError({
                    "actual_flow": "El caudal actual es requerido para válvulas."
                })

            if device_type.device_id == VALVE_48_ID:
                # La válvula de 48" no debe asignarse a ningún predio ni lote
                if id_plot or id_lot:
                    raise serializers.ValidationError(
                        "La válvula de 48\" no puede asignarse a predios ni lotes."
                    )
                
                # Verificar que no exista otra válvula de 48"
                if IoTDevice.objects.filter(device_type_id=VALVE_48_ID).exists():
                    raise serializers.ValidationError(
                        "Ya existe una válvula de 48\" en el sistema."
                    )

            elif device_type.device_id == VALVE_4_ID:
                # Validar que se asigne a un predio o a un lote, pero no a ambos
                if id_plot and id_lot:
                    raise serializers.ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio O a un lote, no a ambos."
                    )
                if not id_plot and not id_lot:
                    raise serializers.ValidationError(
                        "Una válvula de 4\" debe asignarse a un predio o a un lote."
                    )
                
                # Validar que no haya más de una válvula por predio
                if id_plot and not id_lot:
                    if IoTDevice.objects.filter(
                        device_type_id=VALVE_4_ID,
                        id_plot=id_plot,
                        id_lot__isnull=True
                    ).exists():
                        raise serializers.ValidationError(
                            "Ya existe una válvula de 4\" asignada a este predio."
                        )
                
                # Validar que no haya más de una válvula por lote
                if id_lot and not id_plot:
                    if IoTDevice.objects.filter(
                        device_type_id=VALVE_4_ID,
                        id_lot=id_lot,
                        id_plot__isnull=True
                    ).exists():
                        raise serializers.ValidationError(
                            "Ya existe una válvula de 4\" asignada a este lote."
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
    actual_flow = serializers.FloatField(required=True)

    class Meta:
        model = IoTDevice
        fields = ['actual_flow']

    def validate(self, data):
        device = self.instance  # Accede a la instancia actual del dispositivo
        
        if not device:
            raise serializers.ValidationError("Dispositivo no encontrado")
        
        # Valida que el dispositivo sea una válvula usando la instancia, no los datos de entrada
        if device.device_type.device_id not in [VALVE_48_ID, VALVE_4_ID]:
            raise serializers.ValidationError("Solo se puede actualizar el caudal de válvulas.")
        
        if data.get('actual_flow', 0) < 0:
            raise serializers.ValidationError("El caudal no puede ser negativo.")
        
        return data

# class ValveSerializer(serializers.ModelSerializer):
#     id_valve = serializers.CharField(read_only=True)
#     valve_type = serializers.PrimaryKeyRelatedField(queryset=DeviceType.objects.all())
#     id_plot = serializers.PrimaryKeyRelatedField(queryset=Plot.objects.all(), allow_null=True, required=False)
#     id_lot = serializers.PrimaryKeyRelatedField(queryset=Lot.objects.all(), allow_null=True, required=False)

#     class Meta:
#         model = Valve
#         fields = ['id_valve', 'valve_type', 'is_active', 'actual_flow', 'id_plot', 'id_lot']

#     def validate(self, data):
#         id_plot = data.get('id_plot', None)
#         id_lot = data.get('id_lot', None)
#         valve_type = data.get('valve_type')

#         # Validar que si hay lote, pertenezca al predio
#         if id_lot and id_plot and id_lot.plot != id_plot:
#             raise serializers.ValidationError({"id_lot": "El lote no pertenece al predio especificado."})

#         # Validar que no haya más de una válvula del mismo tipo por lote
#         if id_lot and Valve.objects.filter(id_lot=id_lot, valve_type=valve_type).exists():
#             raise serializers.ValidationError({"valve_type": f"Ya existe una válvula {valve_type} en este lote."})

#         return data