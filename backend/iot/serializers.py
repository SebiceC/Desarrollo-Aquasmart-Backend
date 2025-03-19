from rest_framework import serializers
from .models import IoTDevice
from plots_lots.models import Plot, Lot  

class IoTDeviceSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(read_only=True) 

    class Meta:
        model = IoTDevice
        fields = ['id_plot', 'id_lot', 'name', 'device_type', 'is_active', 'characteristics', 'device_id']

    def validate_name(self, value):
        """ Validación para asegurar que el nombre no esté vacío """
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_characteristics(self, value):
        """ Validación para características: obligatorio y máximo 300 caracteres """
        if not value:
            raise serializers.ValidationError("Las características son obligatorias.")
        if len(value) > 300:
            raise serializers.ValidationError("Las características no pueden tener más de 300 caracteres.")
        return value

    def validate(self, data):
        """ Validación personalizada """
        # Validar que el predio (id_plot) y lote (id_lot) existan
        if data.get('id_plot') and not Plot.objects.filter(id_plot=data['id_plot']).exists():
            raise serializers.ValidationError("El predio con el ID proporcionado no existe.")

        if data.get('id_lot') and not Lot.objects.filter(id_lot=data['id_lot']).exists():
            raise serializers.ValidationError("El lote con el ID proporcionado no existe.")

        # Validar que no haya más de un dispositivo del mismo tipo por lote
        if data.get('id_lot'):
            # Buscar dispositivos en el lote con el mismo tipo de dispositivo
            if IoTDevice.objects.filter(id_lot=data['id_lot'], device_type=data['device_type']).exists():
                raise serializers.ValidationError(f"Ya existe un dispositivo {data['device_type']} en este lote.")

        # Validar que el estado sea correcto
        if data.get('is_active') not in [True, False]:
            raise serializers.ValidationError("El estado del dispositivo es obligatorio.")

        return data
