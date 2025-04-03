from rest_framework import serializers
from .models import IoTDevice, DeviceType
from plots_lots.models import Plot, Lot  

class IoTDeviceSerializer(serializers.ModelSerializer):
    iot_id = serializers.CharField(read_only=True)  # ID generado automáticamente
    device_type = serializers.PrimaryKeyRelatedField(queryset=DeviceType.objects.all())  
    id_plot = serializers.PrimaryKeyRelatedField(queryset=Plot.objects.all(), allow_null=True, required=False)  
    id_lot = serializers.PrimaryKeyRelatedField(queryset=Lot.objects.all(), allow_null=True, required=False)  
    owner_name = serializers.CharField(required=False, allow_blank=True)  # ✅ Permite que se envíe en la petición
    device_type_name = serializers.CharField(source='device_type.name', read_only=True)

    class Meta:
        model = IoTDevice
        fields = ['iot_id', 'id_plot', 'id_lot', 'name', 'device_type', 'is_active', 'characteristics', 'owner_name', 'device_type_name']

    def validate(self, data):
        """ Validación personalizada """
        id_plot = data.get('id_plot', None)  
        id_lot = data.get('id_lot', None)  
        device_type = data.get('device_type')
        owner_name = data.get('owner_name', '').strip()

        # 1️⃣ Si `id_plot` tiene dueño y `owner_name` se envía en la petición, lanzar error
        if id_plot and id_plot.owner and owner_name:
            raise serializers.ValidationError({"owner_name": "El propietario ya se obtiene del predio y no debe enviarse manualmente."})

        # 2️⃣ Si `id_lot` está presente, validar que pertenece al `id_plot`
        if id_lot and id_plot and id_lot.plot != id_plot:
            raise serializers.ValidationError({"id_lot": "El lote no pertenece al predio especificado."})

        # 3️⃣ Validar que no haya más de un dispositivo del mismo tipo por lote
        if id_lot and IoTDevice.objects.filter(id_lot=id_lot, device_type=device_type).exists():
            raise serializers.ValidationError({"device_type": f"Ya existe un dispositivo {device_type} en este lote."})

        return data

    def create(self, validated_data):
        """ Crear el dispositivo IoT y establecer el owner_name según disponibilidad """
        id_plot = validated_data.get('id_plot', None)

        # Si `owner_name` no fue enviado y el `plot` tiene dueño, lo asignamos
        if not validated_data.get('owner_name') and id_plot and id_plot.owner:
            validated_data['owner_name'] = id_plot.owner.get_full_name()

        # Si sigue sin valor, asignamos "Sin dueño"
        if not validated_data.get('owner_name'):
            validated_data['owner_name'] = "Sin dueño"

        return IoTDevice.objects.create(**validated_data)

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
